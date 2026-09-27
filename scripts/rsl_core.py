"""
RSL Core v2.1 - Fachlogik ohne GUI
==================================
1:1 aus rsl_gui.py übernommen (Indexlisten, RSLDatabase, RSL-Berechnung, HTML-Report).
Ergänzt: Trades bearbeiten/löschen mit Konsistenzprüfung (FIFO-Reihenfolge).
Wird von rsl_web.py (Web-Version) verwendet.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from threading import Thread
import os, sys, json, webbrowser, warnings

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
    HAS_YF = True
except ImportError:
    HAS_YF = False

try:
    import urllib.request, ssl
    from io import StringIO
    HAS_NET = True
except ImportError:
    HAS_NET = False

warnings.filterwarnings("ignore")

# ============================================================================
# KONSTANTEN
# ============================================================================

C = {
    'bg': '#0f1923', 'card': '#1a2634', 'inp': '#0d1520',
    'acc': '#00d4aa', 'acd': '#00a888', 'red': '#ff4757', 'rdd': '#c0392b',
    'rbg': '#3a1520', 'org': '#ffa502', 'blu': '#3498db',
    'tp': '#e8edf2', 'ts': '#8899aa', 'td': '#556677', 'brd': '#2a3a4a',
    'hdr': '#141e2a', 're': '#1a2634', 'ro': '#1e2d3d',
}

SECTOR_COLORS = {
    'Technology': '#3498db', 'Information Technology': '#3498db',
    'Communication Services': '#9b59b6', 'Consumer Discretionary': '#e74c3c',
    'Consumer Staples': '#27ae60', 'Energy': '#f39c12', 'Financials': '#1abc9c',
    'Healthcare': '#e91e63', 'Health Care': '#e91e63', 'Industrials': '#795548',
    'Materials': '#607d8b', 'Real Estate': '#00bcd4', 'Utilities': '#ff9800',
    'Unknown': '#bdc3c7',
}

SMA_PERIOD = 26
MIN_PERIODS = 21
TOP_PCT = 0.25
SELL_THR = 125

# ============================================================================
# INDEX-DEFINITIONEN
# ============================================================================

INDEX_DEFS = {
    'S&P 500': {
        'wiki_url': 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies',
        'suffix': '', 'col_ticker': 'Symbol', 'col_name': 'Security',
        'col_sector': 'GICS Sector', 'ticker_replace': {'.': '-'},
        'description': 'US Large Cap (500 Aktien)',
    },
    'DAX': {
        'wiki_url': 'https://en.wikipedia.org/wiki/DAX',
        'suffix': '.DE', 'col_ticker': 'Ticker', 'col_name': 'Company',
        'col_sector': 'Prime Standard Sector', 'ticker_replace': {},
        'description': 'Deutschland Top 40',
    },
    'MDAX': {
        'wiki_url': 'https://en.wikipedia.org/wiki/MDAX',
        'suffix': '.DE', 'col_ticker': 'Ticker symbol', 'col_name': 'Company',
        'col_sector': None, 'ticker_replace': {},
        'description': 'Deutschland Mid Cap (50)',
    },
    'TecDAX': {
        'wiki_url': 'https://en.wikipedia.org/wiki/TecDAX',
        'suffix': '.DE', 'col_ticker': 'Ticker symbol', 'col_name': 'Company',
        'col_sector': None, 'ticker_replace': {},
        'description': 'Deutschland Tech (30)',
    },
    'KOSPI 200': {
        'wiki_url': None,
        'suffix': '.KS', 'col_ticker': None, 'col_name': None,
        'col_sector': None, 'ticker_replace': {},
        'description': 'Korea Top 200',
    },
    'Nikkei 225': {
        'wiki_url': 'https://en.wikipedia.org/wiki/Nikkei_225',
        'suffix': '.T', 'col_ticker': 'Ticker', 'col_name': 'Company',
        'col_sector': 'Sector', 'ticker_replace': {},
        'description': 'Japan Top 225',
    },
}


# ============================================================================
# TICKER ABRUF (Statische Listen + S&P 500 Wikipedia-Fallback)
# ============================================================================

def _wiki_sp500():
    """Lädt S&P 500 Ticker von Wikipedia (zuverlässigste Quelle)"""
    if not HAS_NET or not HAS_YF:
        return [], {}
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
                                     headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
            html = r.read().decode('utf-8')
        df = pd.read_html(StringIO(html))[0]
        df.columns = df.columns.str.strip()
        tickers, si = [], {}
        for _, row in df.iterrows():
            t = str(row.get('Symbol', '')).replace('.', '-').strip()
            if t:
                tickers.append(t)
                si[t] = {'name': str(row.get('Security', t)), 'sector': str(row.get('GICS Sector', 'Unknown'))}
        return tickers, si
    except Exception:
        return [], {}


# ---- STATISCHE TICKER-LISTEN ----

_DAX = [
    ('ADS.DE','Adidas','Consumer Discretionary'),('AIR.DE','Airbus','Industrials'),('ALV.DE','Allianz','Financials'),
    ('BAS.DE','BASF','Materials'),('BAYN.DE','Bayer','Healthcare'),('BEI.DE','Beiersdorf','Consumer Staples'),
    ('BMW.DE','BMW','Consumer Discretionary'),('BNR.DE','Brenntag','Industrials'),('CBK.DE','Commerzbank','Financials'),
    ('CON.DE','Continental','Consumer Discretionary'),('DTG.DE','Daimler Truck','Industrials'),
    ('DBK.DE','Deutsche Bank','Financials'),('DB1.DE','Deutsche Börse','Financials'),('DHL.DE','DHL Group','Industrials'),
    ('DTE.DE','Deutsche Telekom','Communication Services'),('EOAN.DE','E.ON','Utilities'),('FRE.DE','Fresenius','Healthcare'),
    ('HNR1.DE','Hannover Rück','Financials'),('HEI.DE','Heidelberg Materials','Materials'),('HEN3.DE','Henkel','Consumer Staples'),
    ('IFX.DE','Infineon','Technology'),('MBG.DE','Mercedes-Benz','Consumer Discretionary'),('MRK.DE','Merck KGaA','Healthcare'),
    ('MTX.DE','MTU Aero Engines','Industrials'),('MUV2.DE','Munich Re','Financials'),('PAH3.DE','Porsche Automobil','Consumer Discretionary'),
    ('P911.DE','Porsche AG','Consumer Discretionary'),('QIA.DE','Qiagen','Healthcare'),('RHM.DE','Rheinmetall','Industrials'),
    ('RWE.DE','RWE','Utilities'),('SAP.DE','SAP','Technology'),('SRT3.DE','Sartorius','Healthcare'),
    ('SIE.DE','Siemens','Industrials'),('ENR.DE','Siemens Energy','Energy'),('SHL.DE','Siemens Healthineers','Healthcare'),
    ('SY1.DE','Symrise','Materials'),('VOW3.DE','Volkswagen','Consumer Discretionary'),('VNA.DE','Vonovia','Real Estate'),
    ('ZAL.DE','Zalando','Consumer Discretionary'),
]

_MDAX = [
    ('AIXA.DE','Aixtron','Technology'),('AM3D.DE','SLM Solutions','Industrials'),('AT1.DE','Aroundtown','Real Estate'),
    ('B4B.DE','Metro','Consumer Staples'),('BC8.DE','Bechtle','Technology'),('BJ4.DE','Bastei Lübbe','Consumer Discretionary'),
    ('BOSS.DE','Hugo Boss','Consumer Discretionary'),('CEC.DE','CropEnergies','Energy'),('COP.DE','Compugroup Medical','Healthcare'),
    ('DEZ.DE','Deutz','Industrials'),('DUE.DE','Dürr','Industrials'),('DHER.DE','Delivery Hero','Technology'),
    ('EVK.DE','Evonik','Materials'),('EVT.DE','Evotec','Healthcare'),('FIE.DE','Fielmann','Healthcare'),
    ('FPE3.DE','Fuchs Petrolub','Materials'),('FRA.DE','Fraport','Industrials'),('G1A.DE','GEA Group','Industrials'),
    ('G24.DE','Scout24','Technology'),('GBF.DE','Bilfinger','Industrials'),('GXI.DE','Gerresheimer','Healthcare'),
    ('HAG.DE','Hensoldt','Industrials'),('HLAG.DE','Hapag-Lloyd','Industrials'),('HLE.DE','Hella','Consumer Discretionary'),
    ('HOT.DE','Hochtief','Industrials'),('JUN3.DE','Jungheinrich','Industrials'),('KCO.DE','Klöckner','Materials'),
    ('KGX.DE','Kion Group','Industrials'),('KRN.DE','K+S','Materials'),('KWS.DE','KWS Saat','Consumer Staples'),
    ('LEG.DE','LEG Immobilien','Real Estate'),('LEO.DE','Leoni','Industrials'),('LXS.DE','Lanxess','Materials'),
    ('MDG1.DE','Medigene','Healthcare'),('NDA.DE','Aurubis','Materials'),('NOEJ.DE','Nordex','Energy'),
    ('O2D.DE','Telefónica Deutschland','Communication Services'),('PBB.DE','PBB Deutsche Pfandbriefbank','Financials'),
    ('PSM.DE','ProSiebenSat.1','Communication Services'),('PUM.DE','Puma','Consumer Discretionary'),
    ('RAA.DE','Rational','Industrials'),('RRTL.DE','RTL Group','Communication Services'),('S92.DE','SMA Solar','Energy'),
    ('SHA.DE','Schaeffler','Consumer Discretionary'),('SZG.DE','Salzgitter','Materials'),('TKA.DE','ThyssenKrupp','Materials'),
    ('TLX.DE','Talanx','Financials'),('WAF.DE','Siltronic','Technology'),('WCH.DE','Wacker Chemie','Materials'),
    ('ZIL2.DE','Elringklinger','Consumer Discretionary'),
]

_TECDAX = [
    ('AIXA.DE','Aixtron','Technology'),('BC8.DE','Bechtle','Technology'),('DHER.DE','Delivery Hero','Technology'),
    ('DRI.DE','Drägerwerk','Healthcare'),('EVT.DE','Evotec','Healthcare'),('FNTN.DE','Freenet','Communication Services'),
    ('G24.DE','Scout24','Technology'),('GXI.DE','Gerresheimer','Healthcare'),('IFX.DE','Infineon','Technology'),
    ('JEN.DE','Jenoptik','Technology'),('MDG1.DE','Medigene','Healthcare'),('MOR.DE','MorphoSys','Healthcare'),
    ('NDX1.DE','Nordex','Energy'),('NEM.DE','Nemetschek','Technology'),('O2D.DE','Telefónica DE','Communication Services'),
    ('PFV.DE','Pfeiffer Vacuum','Industrials'),('QIA.DE','Qiagen','Healthcare'),('RIB.DE','RIB Software','Technology'),
    ('S92.DE','SMA Solar','Energy'),('SAP.DE','SAP','Technology'),('SHL.DE','Siemens Healthineers','Healthcare'),
    ('SIE.DE','Siemens','Technology'),('SRT3.DE','Sartorius','Healthcare'),('UTDI.DE','United Internet','Technology'),
    ('WAF.DE','Siltronic','Technology'),('WCH.DE','Wacker Chemie','Materials'),
    ('1U1.DE','1&1','Communication Services'),('SOW.DE','Software AG','Technology'),('SANT.DE','S&T AG','Technology'),
]

_NIKKEI = [
    ('7203.T','Toyota Motor','Consumer Discretionary'),('6758.T','Sony Group','Technology'),('6861.T','Keyence','Technology'),
    ('8306.T','MUFG','Financials'),('9432.T','NTT','Communication Services'),('6501.T','Hitachi','Industrials'),
    ('6098.T','Recruit Holdings','Industrials'),('8035.T','Tokyo Electron','Technology'),('9984.T','SoftBank Group','Technology'),
    ('7741.T','HOYA','Healthcare'),('4063.T','Shin-Etsu Chemical','Materials'),('6902.T','Denso','Consumer Discretionary'),
    ('4519.T','Chugai Pharma','Healthcare'),('6857.T','Advantest','Technology'),('7974.T','Nintendo','Communication Services'),
    ('8058.T','Mitsubishi Corp','Industrials'),('4568.T','Daiichi Sankyo','Healthcare'),('6920.T','Lasertec','Technology'),
    ('9433.T','KDDI','Communication Services'),('6954.T','Fanuc','Industrials'),('7267.T','Honda Motor','Consumer Discretionary'),
    ('8001.T','Itochu','Industrials'),('8316.T','Sumitomo Mitsui','Financials'),('4502.T','Takeda Pharma','Healthcare'),
    ('9983.T','Fast Retailing','Consumer Discretionary'),('8766.T','Tokio Marine','Financials'),('4661.T','Oriental Land','Consumer Discretionary'),
    ('3382.T','Seven & i','Consumer Staples'),('6762.T','TDK','Technology'),('6367.T','Daikin Industries','Industrials'),
    ('2914.T','Japan Tobacco','Consumer Staples'),('5108.T','Bridgestone','Consumer Discretionary'),('4543.T','Terumo','Healthcare'),
    ('4901.T','Fujifilm','Healthcare'),('6273.T','SMC','Industrials'),('7751.T','Canon','Technology'),
    ('9434.T','SoftBank Corp','Communication Services'),('8031.T','Mitsui & Co','Industrials'),('4578.T','Otsuka Holdings','Healthcare'),
    ('6981.T','Murata Mfg','Technology'),('3407.T','Asahi Kasei','Materials'),('7269.T','Suzuki Motor','Consumer Discretionary'),
    ('6752.T','Panasonic','Consumer Discretionary'),('8411.T','Mizuho Financial','Financials'),('6301.T','Komatsu','Industrials'),
    ('1925.T','Daiwa House','Real Estate'),('4452.T','Kao Corp','Consumer Staples'),('6702.T','Fujitsu','Technology'),
    ('6503.T','Mitsubishi Electric','Industrials'),('7832.T','Bandai Namco','Consumer Discretionary'),('9735.T','Secom','Industrials'),
    ('6723.T','Renesas Electronics','Technology'),('8802.T','Mitsubishi Estate','Real Estate'),('8591.T','Orix','Financials'),
    ('1928.T','Sekisui House','Consumer Discretionary'),('2802.T','Ajinomoto','Consumer Staples'),('4507.T','Shionogi','Healthcare'),
    ('8830.T','Sumitomo Realty','Real Estate'),('6971.T','Kyocera','Technology'),('4503.T','Astellas Pharma','Healthcare'),
    ('8725.T','MS&AD Insurance','Financials'),('6594.T','Nidec','Industrials'),('6506.T','Yaskawa Electric','Industrials'),
    ('3659.T','Nexon','Communication Services'),('8750.T','Dai-ichi Life','Financials'),('7011.T','Mitsubishi Heavy','Industrials'),
    ('5401.T','Nippon Steel','Materials'),('9613.T','NTT Data','Technology'),('7733.T','Olympus','Healthcare'),
    ('4523.T','Eisai','Healthcare'),('2413.T','M3','Healthcare'),('6976.T','Taiyo Yuden','Technology'),
    ('4911.T','Shiseido','Consumer Staples'),('6674.T','GS Yuasa','Industrials'),('2801.T','Kikkoman','Consumer Staples'),
    ('7201.T','Nissan Motor','Consumer Discretionary'),('9020.T','JR East','Industrials'),('9021.T','JR West','Industrials'),
    ('1605.T','INPEX','Energy'),('6326.T','Kubota','Industrials'),('8053.T','Sumitomo Corp','Industrials'),
    ('5713.T','Sumitomo Metal Mining','Materials'),('3086.T','J.Front Retailing','Consumer Discretionary'),
    ('6645.T','Omron','Technology'),('3099.T','Isetan Mitsukoshi','Consumer Discretionary'),('7202.T','Isuzu Motors','Consumer Discretionary'),
    ('7912.T','Dai Nippon Printing','Industrials'),('4704.T','Trend Micro','Technology'),('1802.T','Obayashi Corp','Industrials'),
    ('5020.T','ENEOS Holdings','Energy'),('2502.T','Asahi Group','Consumer Staples'),('1803.T','Shimizu Corp','Industrials'),
    ('4751.T','CyberAgent','Communication Services'),('2503.T','Kirin Holdings','Consumer Staples'),
    ('6988.T','Nitto Denko','Materials'),('7261.T','Mazda Motor','Consumer Discretionary'),('8309.T','Sumitomo Trust','Financials'),
    ('6178.T','Japan Post','Financials'),('9022.T','JR Central','Industrials'),('6701.T','NEC Corp','Technology'),
    ('6504.T','Fuji Electric','Industrials'),('5802.T','Sumitomo Electric','Industrials'),('4021.T','Nissan Chemical','Materials'),
    ('6841.T','Yokogawa Electric','Technology'),('7270.T','Subaru','Consumer Discretionary'),
    ('4755.T','Rakuten Group','Consumer Discretionary'),('6479.T','Minebea Mitsumi','Technology'),
    ('2269.T','Meiji Holdings','Consumer Staples'),('3405.T','Kuraray','Materials'),
    ('9766.T','Konami Group','Communication Services'),('8604.T','Nomura Holdings','Financials'),
    ('5631.T','Japan Steel Works','Industrials'),('4151.T','Kyowa Kirin','Healthcare'),
    ('9531.T','Tokyo Gas','Utilities'),('9502.T','Chubu Electric','Utilities'),('6305.T','Hitachi Construction','Industrials'),
    ('8267.T','Aeon','Consumer Staples'),('4324.T','Dentsu Group','Communication Services'),
    ('6361.T','Ebara Corp','Industrials'),('9101.T','Nippon Yusen','Industrials'),
    ('5332.T','TOTO','Industrials'),('7186.T','Concordia Financial','Financials'),
    ('6113.T','Amada','Industrials'),('7735.T','Screen Holdings','Technology'),
    ('9107.T','Kawasaki Kisen','Industrials'),('3289.T','Tokyu Fudosan','Real Estate'),
    ('4689.T','LY Corp','Technology'),('8354.T','Fukuoka Financial','Financials'),
    ('5803.T','Fujikura','Industrials'),('6753.T','Sharp','Technology'),
    ('9104.T','Mitsui OSK Lines','Industrials'),('2768.T','Sojitz','Industrials'),
    ('6103.T','Okuma','Industrials'),('9001.T','Tobu Railway','Industrials'),
    ('4631.T','DIC Corp','Materials'),('7211.T','Mitsubishi Motors','Consumer Discretionary'),
    ('6302.T','Sumitomo Heavy','Industrials'),('3861.T','Oji Holdings','Materials'),
    ('2871.T','Nichirei','Consumer Staples'),('7731.T','Nikon','Technology'),
    ('9602.T','Toho Co','Communication Services'),('5301.T','Tokai Carbon','Materials'),
    ('2002.T','Nisshin Seifun','Consumer Staples'),('3101.T','Toyobo','Materials'),
    ('4005.T','Sumitomo Chemical','Materials'),('7004.T','Hitachi Zosen','Industrials'),
    ('5201.T','AGC Inc','Materials'),('6471.T','NSK','Industrials'),
    ('4042.T','Tosoh','Materials'),('5406.T','Kobe Steel','Materials'),
    ('6724.T','Seiko Epson','Technology'),('6963.T','Rohm','Technology'),
    ('2531.T','Takara Holdings','Consumer Staples'),('4043.T','Tokuyama','Materials'),
    ('8601.T','Daiwa Securities','Financials'),('3402.T','Toray Industries','Materials'),
    ('7762.T','Citizen Watch','Consumer Discretionary'),('5333.T','NGK Insulators','Industrials'),
    ('1801.T','Taisei Corp','Industrials'),('5411.T','JFE Holdings','Materials'),
    ('4183.T','Mitsui Chemicals','Materials'),('4188.T','Mitsubishi Chemical','Materials'),
    ('8233.T','Takashimaya','Consumer Discretionary'),
    ('9062.T','Nippon Express','Industrials'),
    ('8303.T','Shinsei Bank','Financials'),('2282.T','NH Foods','Consumer Staples'),
    ('3401.T','Teijin','Materials'),('4208.T','UBE Corp','Materials'),
]

_KOSPI = [
    ('005930.KS','Samsung Electronics','Technology'),('000660.KS','SK Hynix','Technology'),
    ('051910.KS','LG Chem','Materials'),('035420.KS','Naver','Communication Services'),
    ('006400.KS','Samsung SDI','Technology'),('035720.KS','Kakao','Communication Services'),
    ('005380.KS','Hyundai Motor','Consumer Discretionary'),('068270.KS','Celltrion','Healthcare'),
    ('028260.KS','Samsung C&T','Industrials'),('105560.KS','KB Financial','Financials'),
    ('012330.KS','Hyundai Mobis','Consumer Discretionary'),('055550.KS','Shinhan Financial','Financials'),
    ('066570.KS','LG Electronics','Consumer Discretionary'),('032830.KS','Samsung Life','Financials'),
    ('003670.KS','POSCO Holdings','Materials'),('096770.KS','SK Innovation','Energy'),
    ('034730.KS','SK Inc','Industrials'),('015760.KS','Korea Electric Power','Utilities'),
    ('017670.KS','SK Telecom','Communication Services'),('033780.KS','KT&G','Consumer Staples'),
    ('003550.KS','LG Corp','Industrials'),('018260.KS','Samsung SDS','Technology'),
    ('086790.KS','Hana Financial','Financials'),('009150.KS','Samsung Electro-Mechanics','Technology'),
    ('011200.KS','HMM','Industrials'),('010130.KS','Korea Zinc','Materials'),
    ('316140.KS','Woori Financial','Financials'),('034020.KS','Doosan Enerbility','Industrials'),
    ('030200.KS','KT Corp','Communication Services'),('000270.KS','Kia','Consumer Discretionary'),
    ('036570.KS','NCsoft','Communication Services'),('251270.KS','Netmarble','Communication Services'),
    ('010950.KS','S-Oil','Energy'),('009540.KS','HD Korea Shipbuilding','Industrials'),
    ('004020.KS','Hyundai Steel','Materials'),('021240.KS','Coway','Consumer Discretionary'),
    ('011170.KS','Lotte Chemical','Materials'),('024110.KS','Industrial Bank of Korea','Financials'),
    ('000810.KS','Samsung Fire & Marine','Financials'),('352820.KS','HYBE','Communication Services'),
    ('010140.KS','Samsung Heavy','Industrials'),('003490.KS','Korean Air','Industrials'),
    ('000720.KS','Hyundai Engineering','Industrials'),('011790.KS','SKC','Materials'),
    ('097950.KS','CJ CheilJedang','Consumer Staples'),('002790.KS','Amore Pacific Group','Consumer Staples'),
    ('047050.KS','POSCO International','Industrials'),('009830.KS','Hanwha Solutions','Industrials'),
    ('161390.KS','Hankook Tire','Consumer Discretionary'),('138040.KS','Meritz Financial','Financials'),
    ('267250.KS','HD Hyundai','Industrials'),('071050.KS','Korea Investment Holdings','Financials'),
    ('001570.KS','Kumho Petrochemical','Materials'),('010120.KS','LS Electric','Industrials'),
    ('006800.KS','Mirae Asset Securities','Financials'),('090430.KS','Amorepacific','Consumer Staples'),
    ('000880.KS','Hanwha Corp','Industrials'),('139480.KS','E-Mart','Consumer Staples'),
    ('047810.KS','Korea Aerospace','Industrials'),('326030.KS','SK Biopharm','Healthcare'),
    ('259960.KS','Krafton','Communication Services'),('011070.KS','LG Innotek','Technology'),
    ('373220.KS','LG Energy Solution','Technology'),('207940.KS','Samsung Biologics','Healthcare'),
    ('302440.KS','SK Bioscience','Healthcare'),('377300.KS','Kakao Pay','Financials'),
]

def fetch_index_tickers(index_name):
    """Lädt Ticker + Sektor-Info für einen Index. Statische Listen für Zuverlässigkeit."""
    if index_name == 'S&P 500':
        tickers, si = _wiki_sp500()
        if len(tickers) > 400:
            return tickers, si
        return [], {}  # S&P nur über Wikipedia, Fallback wäre zu lang

    static_map = {
        'DAX': _DAX, 'MDAX': _MDAX, 'TecDAX': _TECDAX,
        'Nikkei 225': _NIKKEI, 'KOSPI 200': _KOSPI,
    }

    entries = static_map.get(index_name)
    if not entries:
        return [], {}

    tickers = [e[0] for e in entries]
    si = {e[0]: {'name': e[1], 'sector': e[2]} for e in entries}
    return tickers, si


# Globales Namens-Lookup über ALLE statischen Listen
_ALL_NAMES = {}
for _lst in [_DAX, _MDAX, _TECDAX, _NIKKEI, _KOSPI]:
    for _t, _n, _s in _lst:
        _ALL_NAMES[_t] = _n

def ticker_name(ticker, sector_info=None):
    """Gibt Firmennamen für einen Ticker zurück"""
    if sector_info and ticker in sector_info:
        return sector_info[ticker].get('name', ticker)
    return _ALL_NAMES.get(ticker, ticker.replace('.DE', '').replace('.T', '').replace('.KS', ''))


# ============================================================================
# DATENBANK (Multi-Index)
# ============================================================================

class RSLDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self._ensure_tables()
        self._migrate_add_index_column()

    def _conn(self):
        return sqlite3.connect(self.db_path, timeout=10)

    def _ensure_tables(self):
        with self._conn() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS rsl_history (
                ticker TEXT, date TEXT, close_price REAL, sma_value REAL,
                rsl_value REAL, rank INTEGER, total_stocks INTEGER, percentile REAL,
                index_name TEXT DEFAULT 'S&P 500',
                PRIMARY KEY (ticker, date, index_name))""")
            c.execute("""CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT UNIQUE NOT NULL,
                total_shares REAL NOT NULL, avg_buy_price REAL NOT NULL, total_cost REAL NOT NULL,
                first_buy_date TEXT NOT NULL, last_buy_date TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
            c.execute("""CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT NOT NULL, trade_type TEXT NOT NULL,
                trade_date TEXT NOT NULL, price REAL NOT NULL, shares REAL NOT NULL, value REAL NOT NULL,
                rsl_rank_at_trade INTEGER, notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
            c.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT)")

    def _migrate_add_index_column(self):
        """Migration: Stellt sicher dass index_name in PK enthalten ist"""
        with self._conn() as c:
            cols = [r[1] for r in c.execute("PRAGMA table_info(rsl_history)").fetchall()]
            if 'index_name' not in cols:
                # Spalte fehlt komplett → hinzufügen und Tabelle neu aufbauen
                c.execute("ALTER TABLE rsl_history ADD COLUMN index_name TEXT DEFAULT 'S&P 500'")
                c.execute("UPDATE rsl_history SET index_name = 'S&P 500' WHERE index_name IS NULL")
                c.commit()

            # Prüfe ob PK index_name enthält (sonst Konflikte bei Multi-Index)
            # Tabelle neu aufbauen mit korrektem PK
            pk_cols = [r[1] for r in c.execute("PRAGMA table_info(rsl_history)").fetchall() if r[5] > 0]
            if 'index_name' not in pk_cols:
                c.execute("""CREATE TABLE IF NOT EXISTS rsl_history_new (
                    ticker TEXT, date TEXT, close_price REAL, sma_value REAL,
                    rsl_value REAL, rank INTEGER, total_stocks INTEGER, percentile REAL,
                    index_name TEXT DEFAULT 'S&P 500',
                    PRIMARY KEY (ticker, date, index_name))""")
                c.execute("""INSERT OR IGNORE INTO rsl_history_new
                    SELECT ticker, date, close_price, sma_value, rsl_value, rank, total_stocks, percentile, 
                           COALESCE(index_name, 'S&P 500') FROM rsl_history""")
                c.execute("DROP TABLE rsl_history")
                c.execute("ALTER TABLE rsl_history_new RENAME TO rsl_history")
                c.commit()

    # ---- Lesen ----

    def get_all_dates(self, index_name='S&P 500'):
        with self._conn() as c:
            return [r[0] for r in c.execute(
                "SELECT DISTINCT date FROM rsl_history WHERE index_name=? ORDER BY date",
                (index_name,)).fetchall()]

    def get_latest_date(self, index_name='S&P 500'):
        d = self.get_all_dates(index_name)
        return d[-1] if d else None

    def get_available_indices(self):
        """Welche Indizes haben Daten in der DB?"""
        with self._conn() as c:
            return [r[0] for r in c.execute(
                "SELECT DISTINCT index_name FROM rsl_history ORDER BY index_name").fetchall()]

    def get_ranking(self, date=None, index_name='S&P 500', limit=None):
        if date is None:
            date = self.get_latest_date(index_name)
        if not date:
            return []
        q = "SELECT ticker, close_price, sma_value, rsl_value, rank, total_stocks, percentile FROM rsl_history WHERE date=? AND index_name=? ORDER BY rank"
        p = [date, index_name]
        if limit:
            q += " LIMIT ?"
            p.append(limit)
        with self._conn() as c:
            return [dict(zip(['ticker', 'close', 'sma', 'rsl', 'rank', 'total', 'pct'], r))
                    for r in c.execute(q, p).fetchall()]

    def get_rank_changes(self, date=None, weeks_back=1, index_name='S&P 500'):
        dates = self.get_all_dates(index_name)
        if not dates:
            return {}
        if date is None:
            date = dates[-1]
        idx = dates.index(date) if date in dates else len(dates) - 1
        if idx < weeks_back:
            return {}
        prev = dates[idx - weeks_back]
        with self._conn() as c:
            cur = c.execute("""
                SELECT c.ticker, c.rank, p.rank, (p.rank - c.rank)
                FROM rsl_history c JOIN rsl_history p ON c.ticker = p.ticker AND c.index_name = p.index_name
                WHERE c.date=? AND p.date=? AND c.index_name=?""", (date, prev, index_name))
            return {r[0]: {'cur': r[1], 'prev': r[2], 'change': r[3]} for r in cur.fetchall()}

    def get_portfolio(self):
        with self._conn() as c:
            return [dict(zip(['ticker', 'shares', 'avg_price', 'cost', 'first_buy', 'last_buy'], r))
                    for r in c.execute(
                        "SELECT ticker, total_shares, avg_buy_price, total_cost, first_buy_date, last_buy_date FROM portfolio ORDER BY ticker").fetchall()]

    def get_portfolio_with_current(self):
        """Portfolio mit aktuellen Kursen — sucht über ALLE Indizes"""
        portfolio = self.get_portfolio()
        if not portfolio:
            return []
        with self._conn() as c:
            for p in portfolio:
                # Suche neuesten RSL-Eintrag über alle Indizes
                row = c.execute("""SELECT close_price, rank, rsl_value, index_name
                                   FROM rsl_history WHERE ticker=?
                                   ORDER BY date DESC LIMIT 1""", (p['ticker'],)).fetchone()
                if row:
                    p['current_price'] = row[0]
                    p['rank'] = row[1]
                    p['rsl'] = row[2]
                    p['index'] = row[3]
                    p['current_value'] = row[0] * p['shares']
                    p['pl'] = p['current_value'] - p['cost']
                    p['pl_pct'] = (p['pl'] / p['cost'] * 100) if p['cost'] else 0
                    p['sell_signal'] = row[1] > SELL_THR
                else:
                    p.update({'current_price': p['avg_price'], 'rank': None, 'rsl': None,
                              'index': '?', 'current_value': p['avg_price'] * p['shares'],
                              'pl': 0, 'pl_pct': 0, 'sell_signal': False})
        return portfolio

    def get_trades(self):
        with self._conn() as c:
            return [dict(zip(['id', 'ticker', 'type', 'date', 'price', 'shares', 'value', 'rsl_rank', 'notes'], r))
                    for r in c.execute(
                        "SELECT id, ticker, trade_type, trade_date, price, shares, value, rsl_rank_at_trade, notes FROM trades ORDER BY trade_date DESC, id DESC").fetchall()]

    def get_trades_with_pl(self):
        """Trades mit realisierter P&L für Verkäufe"""
        with self._conn() as c:
            all_trades = c.execute(
                "SELECT id, ticker, trade_type, trade_date, price, shares, value, rsl_rank_at_trade, notes FROM trades ORDER BY trade_date, id").fetchall()
        # Berechne laufenden Ø-Kaufpreis pro Ticker
        running = {}  # ticker -> (total_shares, total_cost)
        trade_pl = {}  # trade_id -> pl
        for tid, ticker, ttype, tdate, price, shares, value, rank, notes in all_trades:
            if ticker not in running:
                running[ticker] = [0.0, 0.0]
            if ttype == 'BUY':
                running[ticker][0] += shares
                running[ticker][1] += price * shares
                trade_pl[tid] = None
            elif ttype == 'SELL':
                ts, tc = running[ticker]
                if ts > 0:
                    avg_buy = tc / ts
                    pl = (price - avg_buy) * shares
                    trade_pl[tid] = pl
                    running[ticker][0] -= shares
                    running[ticker][1] -= avg_buy * shares
                else:
                    trade_pl[tid] = None
        # Jetzt Trades in DESC-Reihenfolge mit P&L zurückgeben
        result = []
        for tid, ticker, ttype, tdate, price, shares, value, rank, notes in reversed(all_trades):
            d = dict(zip(['id', 'ticker', 'type', 'date', 'price', 'shares', 'value', 'rsl_rank', 'notes'],
                         [tid, ticker, ttype, tdate, price, shares, value, rank, notes]))
            d['pl'] = trade_pl.get(tid)
            result.append(d)
        return result

    def get_ticker_history(self, ticker, limit=52):
        with self._conn() as c:
            return [dict(zip(['date', 'rsl', 'rank', 'close'], r))
                    for r in c.execute(
                        "SELECT date, rsl_value, rank, close_price FROM rsl_history WHERE ticker=? ORDER BY date DESC LIMIT ?",
                        (ticker, limit)).fetchall()][::-1]

    def get_current_rsl_rank(self, ticker):
        with self._conn() as c:
            row = c.execute("SELECT rank, rsl_value, close_price FROM rsl_history WHERE ticker=? ORDER BY date DESC LIMIT 1",
                            (ticker,)).fetchone()
            return (row[0], row[1], row[2]) if row else (None, None, None)

    def get_summary_stats(self, index_name='S&P 500'):
        date = self.get_latest_date(index_name)
        portfolio = self.get_portfolio_with_current()
        ti = sum(p['cost'] for p in portfolio)
        tv = sum(p.get('current_value', 0) for p in portfolio)
        upl = tv - ti
        closed = self.get_closed_positions()
        rpl = sum(pos['pl'] for pos in closed)
        ranking = self.get_ranking(date, index_name)
        return {
            'date': date or '-', 'total_stocks': len(ranking),
            'total_invested': ti, 'total_value': tv,
            'unrealized_pl': upl, 'unrealized_pl_pct': (upl / ti * 100) if ti else 0,
            'realized_pl': rpl, 'total_pl': upl + rpl,
            'total_pl_pct': ((upl + rpl) / ti * 100) if ti else 0,
            'num_positions': len(portfolio),
            'sell_signals': len([p for p in portfolio if p.get('sell_signal')]),
            'dates_count': len(self.get_all_dates(index_name)),
            'index_name': index_name,
        }

    def get_closed_positions(self):
        with self._conn() as c:
            tickers = [r[0] for r in c.execute("SELECT DISTINCT ticker FROM trades").fetchall()]
            closed = []
            for ticker in tickers:
                trades = c.execute(
                    "SELECT trade_type, trade_date, price, shares FROM trades WHERE ticker=? ORDER BY trade_date, id",
                    (ticker,)).fetchall()
                bq = []
                for tt, td, pr, sh in trades:
                    if tt == 'BUY':
                        bq.append([td, pr, sh])
                    elif tt == 'SELL':
                        to_sell = sh
                        while to_sell > 0 and bq:
                            bd, bp, br = bq[0]
                            m = min(to_sell, br)
                            bv, sv = m * bp, m * pr
                            try:
                                days = (datetime.strptime(td, '%Y-%m-%d') - datetime.strptime(bd, '%Y-%m-%d')).days
                            except Exception:
                                days = 0
                            closed.append({'ticker': ticker, 'buy_date': bd, 'sell_date': td,
                                           'shares': m, 'buy_price': bp, 'sell_price': pr,
                                           'pl': sv - bv, 'pl_pct': ((sv - bv) / bv * 100) if bv else 0, 'days': days})
                            bq[0][2] -= m
                            if bq[0][2] <= 0:
                                bq.pop(0)
                            to_sell -= m
            return closed

    def search_ticker(self, query, index_name='S&P 500'):
        date = self.get_latest_date(index_name)
        if not date:
            return []
        with self._conn() as c:
            return [dict(zip(['ticker', 'close', 'rsl', 'rank'], r))
                    for r in c.execute(
                        "SELECT ticker, close_price, rsl_value, rank FROM rsl_history WHERE date=? AND index_name=? AND ticker LIKE ? ORDER BY rank LIMIT 20",
                        (date, index_name, f'%{query.upper()}%')).fetchall()]

    # ---- Schreiben ----

    def add_trade(self, ticker, trade_type, trade_date, price, shares, notes=''):
        ticker = ticker.upper()
        trade_type = trade_type.upper()
        value = price * shares
        rank, _, _ = self.get_current_rsl_rank(ticker)
        with self._conn() as c:
            c.execute("INSERT INTO trades (ticker, trade_type, trade_date, price, shares, value, rsl_rank_at_trade, notes) VALUES (?,?,?,?,?,?,?,?)",
                      (ticker, trade_type, trade_date, price, shares, value, rank, notes))
            self._update_portfolio(c, ticker)
            c.commit()

    def _update_portfolio(self, conn, ticker):
        trades = conn.execute("SELECT trade_type, trade_date, price, shares FROM trades WHERE ticker=? ORDER BY trade_date, id",
                              (ticker,)).fetchall()
        if not trades:
            conn.execute("DELETE FROM portfolio WHERE ticker=?", (ticker,))
            return
        ts, tc, fb, lb = 0.0, 0.0, None, None
        for tt, td, pr, sh in trades:
            if tt == 'BUY':
                ts += sh; tc += pr * sh
                if fb is None: fb = td
                lb = td
            elif tt == 'SELL' and ts > 0:
                avg = tc / ts; ts -= sh; tc -= avg * sh
        if ts <= 0:
            conn.execute("DELETE FROM portfolio WHERE ticker=?", (ticker,))
        else:
            conn.execute("INSERT OR REPLACE INTO portfolio (ticker,total_shares,avg_buy_price,total_cost,first_buy_date,last_buy_date,updated_at) VALUES (?,?,?,?,?,?,datetime('now'))",
                         (ticker, ts, tc / ts if ts > 0 else 0, tc, fb, lb))

    def save_ranking(self, date_str, ranking_df, index_name='S&P 500'):
        with self._conn() as c:
            c.execute("DELETE FROM rsl_history WHERE date=? AND index_name=?", (date_str, index_name))
            total = len(ranking_df)
            for ticker, row in ranking_df.iterrows():
                rank = int(row['Rang'])
                c.execute("INSERT OR REPLACE INTO rsl_history (ticker,date,close_price,sma_value,rsl_value,rank,total_stocks,percentile,index_name) VALUES (?,?,?,?,?,?,?,?,?)",
                          (ticker, date_str, row['Schlusskurs'], row['SMA-26'], row['RSL-Wert'], rank, total, round(rank / total * 100, 1), index_name))
            c.commit()

    # ---- Trades bearbeiten / löschen (Web-Version) ----

    def get_trade(self, trade_id):
        with self._conn() as c:
            r = c.execute("SELECT id, ticker, trade_type, trade_date, price, shares, value, rsl_rank_at_trade, notes FROM trades WHERE id=?",
                          (trade_id,)).fetchone()
        return dict(zip(['id', 'ticker', 'type', 'date', 'price', 'shares', 'value', 'rsl_rank', 'notes'], r)) if r else None

    @staticmethod
    def _check_sequence(conn, ticker):
        """Prüft chronologisch (FIFO-Reihenfolge wie _update_portfolio), dass kein Verkauf
        mehr Stück verkauft als zu diesem Zeitpunkt vorhanden sind. Gibt Fehlertext oder None zurück."""
        held = 0.0
        for tt, td, sh in conn.execute(
                "SELECT trade_type, trade_date, shares FROM trades WHERE ticker=? ORDER BY trade_date, id", (ticker,)):
            if tt == 'BUY':
                held += sh
            elif tt == 'SELL':
                if sh > held + 1e-9:
                    return (f"{ticker}: Verkauf am {td} über {sh:g} Stück, "
                            f"zu diesem Zeitpunkt sind nur {held:g} Stück im Bestand.")
                held -= sh
        return None

    def add_trade_checked(self, ticker, trade_type, trade_date, price, shares, notes=''):
        """Wie add_trade(), aber mit Konsistenzprüfung. Gibt (ok, msg) zurück."""
        ticker = ticker.upper(); trade_type = trade_type.upper()
        rank, _, _ = self.get_current_rsl_rank(ticker)
        c = self._conn()
        try:
            c.execute("INSERT INTO trades (ticker, trade_type, trade_date, price, shares, value, rsl_rank_at_trade, notes) VALUES (?,?,?,?,?,?,?,?)",
                      (ticker, trade_type, trade_date, price, shares, price * shares, rank, notes))
            err = self._check_sequence(c, ticker)
            if err:
                c.rollback(); return False, err
            self._update_portfolio(c, ticker)
            c.commit(); return True, "Trade gebucht."
        finally:
            c.close()

    def update_trade(self, trade_id, ticker, trade_type, trade_date, price, shares, notes=''):
        """Trade ändern. Portfolio wird für alten UND neuen Ticker neu berechnet. Gibt (ok, msg) zurück."""
        old = self.get_trade(trade_id)
        if not old:
            return False, "Trade nicht gefunden."
        ticker = ticker.upper(); trade_type = trade_type.upper()
        rank = old['rsl_rank']
        if ticker != old['ticker']:
            rank, _, _ = self.get_current_rsl_rank(ticker)
        c = self._conn()
        try:
            c.execute("UPDATE trades SET ticker=?, trade_type=?, trade_date=?, price=?, shares=?, value=?, rsl_rank_at_trade=?, notes=? WHERE id=?",
                      (ticker, trade_type, trade_date, price, shares, price * shares, rank, notes, trade_id))
            for t in {old['ticker'], ticker}:
                err = self._check_sequence(c, t)
                if err:
                    c.rollback(); return False, err
            for t in {old['ticker'], ticker}:
                self._update_portfolio(c, t)
            c.commit(); return True, "Trade geändert."
        finally:
            c.close()

    def delete_trade(self, trade_id):
        """Trade löschen. Abgelehnt, wenn danach ein späterer Verkauf nicht mehr gedeckt wäre."""
        old = self.get_trade(trade_id)
        if not old:
            return False, "Trade nicht gefunden."
        c = self._conn()
        try:
            c.execute("DELETE FROM trades WHERE id=?", (trade_id,))
            err = self._check_sequence(c, old['ticker'])
            if err:
                c.rollback(); return False, err + " Lösche zuerst den Verkauf."
            self._update_portfolio(c, old['ticker'])
            c.commit(); return True, "Trade gelöscht."
        finally:
            c.close()

    def recalculate_all_portfolios(self):
        with self._conn() as c:
            tickers = set(r[0] for r in c.execute("SELECT DISTINCT ticker FROM trades").fetchall())
            pf_tickers = set(r[0] for r in c.execute("SELECT ticker FROM portfolio").fetchall())
            changes = []
            for ticker in tickers | pf_tickers:
                self._update_portfolio(c, ticker)
                row = c.execute("SELECT total_shares FROM portfolio WHERE ticker=?", (ticker,)).fetchone()
                changes.append(f"{ticker}: {row[0]:.0f} Stück" if row else f"{ticker}: entfernt")
            c.commit()
            return changes


# ============================================================================
# RSL BERECHNUNG
# ============================================================================

def calculate_rsl_update(db, index_name='S&P 500', progress_cb=None, status_cb=None):
    if not HAS_YF:
        return False, "yfinance nicht installiert!\npip install yfinance pandas lxml"
    def prog(p):
        if progress_cb: progress_cb(p)
    def stat(m):
        if status_cb: status_cb(m)

    stat(f"Lade {index_name} Ticker...")
    prog(5)
    tickers, sector_info = fetch_index_tickers(index_name)
    if not tickers:
        return False, f"Keine Ticker für {index_name} gefunden.\nWikipedia evtl. nicht erreichbar."

    stat(f"Lade Kursdaten für {len(tickers)} Aktien...")
    prog(10)
    try:
        data = yf.download(tickers, period="2y", interval="1wk", auto_adjust=True, progress=False, threads=True, timeout=60)
    except Exception as e:
        return False, f"Yahoo Finance Fehler:\n{e}"

    if data is None or data.empty:
        return False, "Keine Daten empfangen.\nPrüfe Internetverbindung und Ticker-Symbole."

    # Handle single-ticker case and column structure
    try:
        if isinstance(data.columns, pd.MultiIndex):
            if 'Close' not in data.columns.get_level_values(0):
                return False, "Keine Close-Daten in den heruntergeladenen Daten."
            close = data['Close'].dropna(axis=1, how='all').ffill()
        else:
            if 'Close' not in data.columns:
                return False, "Keine Close-Daten."
            close = data[['Close']].ffill()
            close.columns = tickers[:1]
    except Exception as e:
        return False, f"Datenverarbeitung fehlgeschlagen:\n{e}"

    if close.empty or len(close.columns) < 3:
        return False, f"Nur {len(close.columns) if not close.empty else 0} Aktien mit Daten.\nPrüfe ob der Index korrekte Ticker enthält."

    prog(50)
    stat(f"{len(close.columns)} Aktien geladen. Berechne RSL...")

    sma = close.rolling(window=SMA_PERIOD, min_periods=MIN_PERIODS).mean()
    rsl = close / sma
    vt = len(close.columns) * 0.5  # 50% threshold for smaller indices
    vi = rsl.notna().sum(axis=1)
    rsl = rsl.loc[vi[vi >= vt].index]
    close = close.loc[rsl.index]

    total_dates = len(rsl)
    if total_dates == 0:
        return False, "Keine gültigen RSL-Daten berechnet."

    stat(f"Speichere {total_dates} Wochen-Rankings...")
    for i, date in enumerate(rsl.index):
        rv, cv, sv = rsl.loc[date], close.loc[date], sma.loc[date]
        valid = rv.notna() & (rv > 0) & (rv < 10)
        rdf = pd.DataFrame({'Schlusskurs': cv[valid], 'SMA-26': sv[valid], 'RSL-Wert': rv[valid]})
        rdf = rdf.sort_values('RSL-Wert', ascending=False)
        rdf.insert(0, 'Rang', range(1, len(rdf) + 1))
        if not rdf.empty:
            db.save_ranking(date.strftime('%Y-%m-%d'), rdf, index_name)
        prog(50 + int((i + 1) / total_dates * 45))
        if (i + 1) % 10 == 0:
            stat(f"{index_name}: {i + 1}/{total_dates} Wochen...")

    prog(100)
    dates = db.get_all_dates(index_name)
    rk = db.get_ranking(index_name=index_name)
    return True, f"{index_name} Update abgeschlossen!\n{len(rk)} Aktien, {len(dates)} Wochen Historie."


# ============================================================================
# HTML-REPORT (gekürzt, funktional identisch)
# ============================================================================

def generate_html_report(db, index_name='S&P 500', sector_info=None, open_browser=False):
    date = db.get_latest_date(index_name)
    if not date:
        return None, "Keine Daten vorhanden."
    ranking = db.get_ranking(date, index_name)
    if not ranking:
        return None, "Ranking leer."
    total = len(ranking)
    threshold = int(total * TOP_PCT)
    dates = db.get_all_dates(index_name)
    ch1 = db.get_rank_changes(date, 1, index_name)
    ch4 = db.get_rank_changes(date, 4, index_name)
    portfolio = db.get_portfolio_with_current()
    closed = db.get_closed_positions()
    si = sector_info or {}

    ti = sum(p['cost'] for p in portfolio)
    tv = sum(p.get('current_value', 0) for p in portfolio)
    upl = tv - ti; rpl = sum(p['pl'] for p in closed)

    chart_data = {}
    for r in ranking[:10]:
        h = db.get_ticker_history(r['ticker'], 52)
        if h:
            chart_data[r['ticker']] = {'dates': [x['date'] for x in h], 'ranks': [x['rank'] for x in h], 'rsl': [round(x['rsl'], 4) for x in h]}

    def fc(v):
        if v is None: return '-'
        if v > 0: return f'<span style="color:#28a745">↑{v}</span>'
        if v < 0: return f'<span style="color:#dc3545">↓{abs(v)}</span>'
        return '→'

    rows = ""
    for r in ranking:
        c1 = ch1.get(r['ticker'], {}).get('change')
        c4 = ch4.get(r['ticker'], {}).get('change')
        rows += f'<tr><td>{r["rank"]}</td><td><b>{r["ticker"]}</b></td><td>${r["close"]:.2f}</td><td class="{"positive" if r["rsl"]>1 else "negative"}">{r["rsl"]:.3f}</td><td>{fc(c1)}</td><td>{fc(c4)}</td></tr>'

    phtml = ""
    if portfolio:
        phtml += f'<div class="card"><h2>💼 Portfolio</h2><p>Investiert: ${ti:,.0f} | Marktwert: ${tv:,.0f} | Unrealisiert: <span style="color:{"#28a745" if upl>=0 else "#dc3545"}">${upl:+,.0f}</span> | Realisiert: <span style="color:{"#28a745" if rpl>=0 else "#dc3545"}">${rpl:+,.0f}</span></p>'
        phtml += '<table><thead><tr><th>Ticker</th><th>Stück</th><th>Ø Kauf</th><th>Aktuell</th><th>P&L</th><th>Rang</th></tr></thead><tbody>'
        for p in portfolio:
            pc = '#28a745' if p['pl'] >= 0 else '#dc3545'
            phtml += f'<tr><td><b>{p["ticker"]}</b></td><td>{p["shares"]:.0f}</td><td>${p["avg_price"]:.2f}</td><td>${p.get("current_price",0):.2f}</td><td style="color:{pc}">${p["pl"]:+,.0f} ({p["pl_pct"]:+.1f}%)</td><td>{p.get("rank","-")}</td></tr>'
        phtml += '</tbody></table></div>'

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>RSL {index_name} - {date}</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>*{{box-sizing:border-box}}body{{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#1a1a2e,#16213e);padding:20px;margin:0;color:#ccc}}
.container{{max-width:1400px;margin:0 auto}}.header{{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:30px;border-radius:15px;text-align:center;margin-bottom:20px}}
.header h1{{font-size:2.2em;margin-bottom:5px}}.card{{background:#fff;border-radius:15px;padding:25px;margin-bottom:20px;color:#333}}
.card h2{{color:#333;margin-top:0;border-bottom:2px solid #667eea;padding-bottom:10px}}
table{{width:100%;border-collapse:collapse;font-size:.95em}}th{{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:12px;text-align:left}}
td{{padding:10px;border-bottom:1px solid #eee}}tr:hover{{background:#f0f0f0}}.positive{{color:#28a745}}.negative{{color:#dc3545}}
.chart-container{{height:400px;margin:20px 0}}.search-box{{width:100%;padding:10px;border:2px solid #eee;border-radius:8px;font-size:1em;margin-bottom:15px}}
.table-wrapper{{max-height:600px;overflow-y:auto}}</style></head>
<body><div class="container">
<div class="header"><h1>📈 RSL Report — {index_name}</h1><p>{datetime.now().strftime('%d.%m.%Y %H:%M')} | {total} Aktien | {len(dates)} Wochen</p></div>
{phtml}
<div class="card"><h2>📊 Top 10 Rang-Entwicklung</h2><div id="rc" class="chart-container"></div></div>
<div class="card"><h2>📋 Ranking ({total} Aktien)</h2>
<input type="text" class="search-box" id="sb" placeholder="🔍 Ticker suchen..." onkeyup="ft()">
<div class="table-wrapper"><table id="rt"><thead><tr><th>Rang</th><th>Ticker</th><th>Kurs</th><th>RSL</th><th>1W</th><th>4W</th></tr></thead><tbody>{rows}</tbody></table></div></div>
</div><script>
const cd={json.dumps(chart_data)};const t=[];for(const[k,v] of Object.entries(cd))t.push({{x:v.dates,y:v.ranks,name:k,type:'scatter',mode:'lines+markers'}});
if(t.length)Plotly.newPlot('rc',t,{{yaxis:{{autorange:'reversed',title:'Rang'}},legend:{{orientation:'h',y:-.2}},margin:{{t:20}}}},{{responsive:true}});
function ft(){{const v=document.getElementById('sb').value.toUpperCase();const r=document.getElementById('rt').getElementsByTagName('tr');for(let i=1;i<r.length;i++){{const c=r[i].getElementsByTagName('td')[1];r[i].style.display=c&&c.textContent.toUpperCase().includes(v)?'':'none'}}}};
</script></body></html>"""
    fpath = Path(db.db_path).parent / f"RSL_{index_name.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(html)
    if open_browser:
        webbrowser.open('file://' + str(fpath.resolve()))
    return str(fpath), f"Report: {fpath}"
