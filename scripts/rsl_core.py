"""
RSL Core - Indexlisten und Ticker-Abruf
=======================================
Urspruenglich aus der Desktop-Version (rsl_gui.py) uebernommen. Fuer die
Website werden nur noch die Konstanten, INDEX_DEFS, die festen Ersatzlisten
und der Ticker-Abruf gebraucht; Datenbank, Trades und HTML-Report sind
entfernt.
"""

import urllib.request
from io import StringIO

import pandas as pd

# ============================================================================
# KONSTANTEN
# ============================================================================

SMA_PERIOD = 26
MIN_PERIODS = 21
TOP_PCT = 0.25

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
        'wiki_url': 'https://de.wikipedia.org/wiki/TecDAX',
        'suffix': '.DE', 'col_ticker': 'Symbol', 'col_name': 'Name',
        'col_sector': 'Branche', 'ticker_replace': {},
        'description': 'Deutschland Tech (30)',
    },
    'KOSPI 200': {
        'wiki_url': 'https://en.wikipedia.org/wiki/KOSPI_200',
        'suffix': '.KS', 'col_ticker': 'Symbol', 'col_name': 'Company',
        'col_sector': 'GICS Sector', 'ticker_replace': {}, 'code_digits': 6,
        'description': 'Korea Top 200',
    },
    'Nikkei 225': {
        # Wikipedia fuehrt die Mitglieder nicht mehr - offizielle Liste von Nikkei
        'list_url': 'https://indexes.nikkei.co.jp/en/nkave/index/component?idx=nk225',
        'suffix': '.T',
        'description': 'Japan Top 225',
    },
}


# ============================================================================
# TICKER ABRUF (Statische Listen + S&P 500 Wikipedia-Fallback)
# ============================================================================

def _wiki_sp500():
    """Lädt S&P 500 Ticker von Wikipedia (zuverlässigste Quelle)"""
    try:
        req = urllib.request.Request("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
                                     headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as r:
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
    ('AIXA.DE','Aixtron SE','Halbleiterindustrie'),('AOF.DE','Atoss Software AG','Software'),('BC8.DE','Bechtle AG','IT-Dienstleistungen'),
    ('AFX.DE','Carl Zeiss Meditec AG','Medizintechnik'),('DTE.DE','Deutsche Telekom AG','Telekommunikation'),('DRW3.DE','Drägerwerk AG & Co. KGaA','Medizintechnik'),
    ('EUZ.DE','Eckert & Ziegler Strahlen- und Medizintechnik AG','Medizintechnik'),('ELG.DE','Elmos Semiconductor SE','Halbleiterhersteller'),('EVT.DE','Evotec SE','Biotechnologie'),
    ('FNTN.DE','Freenet AG','Telekommunikation'),('HAG.DE','Hensoldt AG','Luft- und Raumfahrttechnik, Rüstungsindustrie'),('IFX.DE','Infineon Technologies AG','Halbleiterindustrie'),
    ('IOS.DE','Ionos SE','IT-Dienstleistungen'),('JEN.DE','Jenoptik AG','Optik und Elektronik'),('KTN.DE','Kontron AG','eingebettete Rechnertechnologie'),
    ('NEM.DE','Nemetschek SE','Software für Bauwesen'),('NDX1.DE','Nordex SE','Anlagenbau'),('OHB.DE','OHB SE','Raumfahrt- und Technologiekonzern'),
    ('OBCK.DE','Ottobock SE & Co. KGaA','Orthopädie'),('TPE.DE','PVA TePla AG','Maschinenbau'),('QIA.DE','Qiagen N.V.','Biotechnologie'),
    ('SAP.DE','SAP SE','Software'),('SRT3.DE','Sartorius AG','Biotechnologie, Mechatronik'),('SHL.DE','Siemens Healthineers AG','Medizintechnik'),
    ('WAF.DE','Siltronic AG','Halbleiterindustrie'),('S92.DE','SMA Solar Technology AG','Solartechnik'),('SMHN.DE','Suss Microtec SE','Halbleiterindustrie'),
    ('TMV.DE','TeamViewer AG','Software'),('UTDI.DE','United Internet AG','Internet-Provider'),('VBK.DE','Verbio SE','Bioenergie'),
]

_NIKKEI = [
    ('285A.T','KIOXIA HOLDINGS CORP.','Electric Machinery'),('4062.T','IBIDEN CO., LTD.','Electric Machinery'),('6479.T','MINEBEA MITSUMI INC.','Electric Machinery'),
    ('6501.T','HITACHI, LTD.','Electric Machinery'),('6503.T','MITSUBISHI ELECTRIC CORP.','Electric Machinery'),('6504.T','FUJI ELECTRIC CO., LTD.','Electric Machinery'),
    ('6506.T','YASKAWA ELECTRIC CORP.','Electric Machinery'),('6525.T','KOKUSAI ELECTRIC CORP.','Electric Machinery'),('6526.T','SOCIONEXT INC.','Electric Machinery'),
    ('6645.T','OMRON CORP.','Electric Machinery'),('6701.T','NEC CORP.','Electric Machinery'),('6702.T','FUJITSU LTD.','Electric Machinery'),
    ('6723.T','RENESAS ELECTRONICS CORP.','Electric Machinery'),('6724.T','SEIKO EPSON CORP.','Electric Machinery'),('6752.T','PANASONIC HOLDINGS CORP.','Electric Machinery'),
    ('6753.T','SHARP CORP.','Electric Machinery'),('6758.T','SONY GROUP CORP.','Electric Machinery'),('6762.T','TDK CORP.','Electric Machinery'),
    ('6770.T','ALPS ALPINE CO., LTD.','Electric Machinery'),('6841.T','YOKOGAWA ELECTRIC CORP.','Electric Machinery'),('6857.T','ADVANTEST CORP.','Electric Machinery'),
    ('6861.T','KEYENCE CORP.','Electric Machinery'),('6902.T','DENSO CORP.','Electric Machinery'),('6920.T','LASERTEC CORP.','Electric Machinery'),
    ('6954.T','FANUC CORP.','Electric Machinery'),('6963.T','ROHM CO., LTD.','Electric Machinery'),('6971.T','KYOCERA CORP.','Electric Machinery'),
    ('6976.T','TAIYO YUDEN CO., LTD.','Electric Machinery'),('6981.T','MURATA MANUFACTURING CO., LTD.','Electric Machinery'),('7735.T','SCREEN HOLDINGS CO., LTD.','Electric Machinery'),
    ('7751.T','CANON INC.','Electric Machinery'),('7752.T','RICOH CO., LTD.','Electric Machinery'),('8035.T','TOKYO ELECTRON LTD.','Electric Machinery'),
    ('7201.T','NISSAN MOTOR CO., LTD.','Automobiles & Auto parts'),('7202.T','ISUZU MOTORS LTD.','Automobiles & Auto parts'),('7203.T','TOYOTA MOTOR CORP.','Automobiles & Auto parts'),
    ('7211.T','MITSUBISHI MOTORS CORP.','Automobiles & Auto parts'),('7261.T','MAZDA MOTOR CORP.','Automobiles & Auto parts'),('7267.T','HONDA MOTOR CO., LTD.','Automobiles & Auto parts'),
    ('7269.T','SUZUKI MOTOR CORP.','Automobiles & Auto parts'),('7270.T','SUBARU CORP.','Automobiles & Auto parts'),('7272.T','YAMAHA MOTOR CO., LTD.','Automobiles & Auto parts'),
    ('4543.T','TERUMO CORP.','Precision Instruments'),('6146.T','DISCO CORP.','Precision Instruments'),('7731.T','NIKON CORP.','Precision Instruments'),
    ('7733.T','OLYMPUS CORP.','Precision Instruments'),('7741.T','HOYA CORP.','Precision Instruments'),('2432.T','DENA CO., LTD.','Information and Communications'),
    ('3659.T','NEXON CO., LTD.','Information and Communications'),('3697.T','SHIFT INC.','Information and Communications'),('4307.T','NOMURA RESEARCH INSTITUTE, LTD.','Information and Communications'),
    ('4385.T','MERCARI, INC.','Information and Communications'),('4689.T','LY CORP.','Information and Communications'),('4704.T','TREND MICRO INC.','Information and Communications'),
    ('7974.T','NINTENDO CO., LTD.','Information and Communications'),('9432.T','NTT, INC.','Information and Communications'),('9433.T','KDDI CORP.','Information and Communications'),
    ('9434.T','SOFTBANK CORP.','Information and Communications'),('9602.T','TOHO CO., LTD','Information and Communications'),('9697.T','CAPCOM CO., LTD.','Information and Communications'),
    ('9766.T','KONAMI GROUP CORP.','Information and Communications'),('9984.T','SOFTBANK GROUP CORP.','Information and Communications'),('5831.T','SHIZUOKA FINANCIAL GROUP, INC.','Banking'),
    ('7186.T','YOKOHAMA FINANCIAL GROUP, INC.','Banking'),('8304.T','AOZORA BANK, LTD.','Banking'),('8306.T','MITSUBISHI UFJ FINANCIAL GROUP, INC.','Banking'),
    ('8308.T','RESONA HOLDINGS, INC.','Banking'),('8309.T','SUMITOMO MITSUI TRUST GROUP, INC.','Banking'),('8316.T','SUMITOMO MITSUI FINANCIAL GROUP, INC.','Banking'),
    ('8331.T','THE CHIBA BANK, LTD.','Banking'),('8354.T','FUKUOKA FINANCIAL GROUP, INC.','Banking'),('8411.T','MIZUHO FINANCIAL GROUP, INC.','Banking'),
    ('8253.T','CREDIT SAISON CO., LTD.','Other Financial Services'),('8591.T','ORIX CORP.','Other Financial Services'),('8697.T','JAPAN EXCHANGE GROUP, INC.','Other Financial Services'),
    ('8601.T','DAIWA SECURITIES GROUP INC.','Securities'),('8604.T','NOMURA HOLDINGS, INC.','Securities'),('8630.T','SOMPO HOLDINGS, INC.','Insurance'),
    ('8725.T','MS&AD INSURANCE GROUP HOLDINGS, INC.','Insurance'),('8750.T','DAIICHI LIFE GROUP, INC.','Insurance'),('8766.T','TOKIO MARINE HOLDINGS, INC.','Insurance'),
    ('8795.T','T&D HOLDINGS, INC.','Insurance'),('1332.T','NISSUI CORP.','Fishery'),('2002.T','NISSHIN SEIFUN GROUP INC.','Foods'),
    ('2269.T','MEIJI HOLDINGS CO., LTD.','Foods'),('2282.T','NH FOODS LTD.','Foods'),('2501.T','SAPPORO BREWERIES LTD.','Foods'),
    ('2502.T','ASAHI GROUP HOLDINGS, LTD.','Foods'),('2503.T','KIRIN HOLDINGS CO., LTD.','Foods'),('2801.T','KIKKOMAN CORP.','Foods'),
    ('2802.T','AJINOMOTO CO., INC.','Foods'),('2871.T','NICHIREI CORP.','Foods'),('2914.T','JAPAN TOBACCO INC.','Foods'),
    ('4151.T','KYOWA KIRIN CO., LTD.','Pharmaceuticals'),('4502.T','TAKEDA PHARMACEUTICAL CO., LTD.','Pharmaceuticals'),('4503.T','ASTELLAS PHARMA INC.','Pharmaceuticals'),
    ('4506.T','SUMITOMO PHARMA CO., LTD.','Pharmaceuticals'),('4507.T','SHIONOGI & CO., LTD.','Pharmaceuticals'),('4519.T','CHUGAI PHARMACEUTICAL CO., LTD.','Pharmaceuticals'),
    ('4523.T','EISAI CO., LTD.','Pharmaceuticals'),('4568.T','DAIICHI SANKYO CO., LTD.','Pharmaceuticals'),('4578.T','OTSUKA HOLDINGS CO., LTD.','Pharmaceuticals'),
    ('3086.T','J.FRONT RETAILING CO., LTD.','Retail'),('3092.T','ZOZO, INC.','Retail'),('3099.T','ISETAN MITSUKOSHI HOLDINGS LTD.','Retail'),
    ('3382.T','SEVEN & I HOLDINGS CO., LTD.','Retail'),('7453.T','RYOHIN KEIKAKU CO., LTD.','Retail'),('7532.T','PAN PACIFIC INTERNATIONAL HOLDINGS CORP.','Retail'),
    ('8233.T','TAKASHIMAYA CO., LTD.','Retail'),('8252.T','MARUI GROUP CO., LTD.','Retail'),('8267.T','AEON CO., LTD.','Retail'),
    ('9843.T','NITORI HOLDINGS CO., LTD.','Retail'),('9983.T','FAST RETAILING CO., LTD.','Retail'),('2413.T','M3, INC.','Services'),
    ('4324.T','DENTSU GROUP INC.','Services'),('4661.T','ORIENTAL LAND CO., LTD.','Services'),('4751.T','CYBERAGENT, INC.','Services'),
    ('4755.T','RAKUTEN GROUP, INC.','Services'),('6098.T','RECRUIT HOLDINGS CO., LTD.','Services'),('6178.T','JAPAN POST HOLDINGS CO., LTD.','Services'),
    ('6532.T','BAYCURRENT, INC.','Services'),('9735.T','SECOM CO., LTD.','Services'),('1605.T','INPEX CORP.','Mining'),
    ('3401.T','TEIJIN LTD.','Textiles & Apparel'),('3402.T','TORAY INDUSTRIES, INC.','Textiles & Apparel'),('3861.T','OJI HOLDINGS CORP.','Pulp & Paper'),
    ('3405.T','KURARAY CO., LTD.','Chemicals'),('3407.T','ASAHI KASEI CORP.','Chemicals'),('4004.T','RESONAC HOLDINGS CORP.','Chemicals'),
    ('4005.T','SUMITOMO CHEMICAL CO., LTD.','Chemicals'),('4021.T','NISSAN CHEMICAL CORP.','Chemicals'),('4042.T','TOSOH CORP.','Chemicals'),
    ('4043.T','TOKUYAMA CORP.','Chemicals'),('4061.T','DENKA CO., LTD.','Chemicals'),('4063.T','SHIN-ETSU CHEMICAL CO., LTD.','Chemicals'),
    ('4183.T','MITSUI CHEMICALS, INC.','Chemicals'),('4188.T','MITSUBISHI CHEMICAL GROUP CORP.','Chemicals'),('4208.T','UBE CORP.','Chemicals'),
    ('4452.T','KAO CORP.','Chemicals'),('4901.T','FUJIFILM HOLDINGS CORP.','Chemicals'),('4911.T','SHISEIDO CO., LTD.','Chemicals'),
    ('6988.T','NITTO DENKO CORP.','Chemicals'),('5019.T','IDEMITSU KOSAN CO., LTD.','Petroleum'),('5020.T','ENEOS HOLDINGS, INC.','Petroleum'),
    ('5101.T','THE YOKOHAMA RUBBER CO., LTD.','Rubber'),('5108.T','BRIDGESTONE CORP.','Rubber'),('5201.T','AGC INC.','Glass & Ceramics'),
    ('5214.T','NIPPON ELECTRIC GLASS CO., LTD.','Glass & Ceramics'),('5233.T','TAIHEIYO CEMENT CORP.','Glass & Ceramics'),('5301.T','TOKAI CARBON CO., LTD.','Glass & Ceramics'),
    ('5332.T','TOTO LTD.','Glass & Ceramics'),('5333.T','NGK CORP.','Glass & Ceramics'),('5401.T','NIPPON STEEL CORP.','Steel'),
    ('5406.T','KOBE STEEL, LTD.','Steel'),('5411.T','JFE HOLDINGS, INC.','Steel'),('3436.T','SUMCO CORP.','Nonferrous Metals'),
    ('5016.T','JX ADVANCED METALS CORP.','Nonferrous Metals'),('5706.T','MITSUI KINZOKU CO., LTD.','Nonferrous Metals'),('5711.T','MITSUBISHI MATERIALS CORP.','Nonferrous Metals'),
    ('5713.T','SUMITOMO METAL MINING CO., LTD.','Nonferrous Metals'),('5714.T','DOWA HOLDINGS CO., LTD.','Nonferrous Metals'),('5801.T','FURUKAWA ELECTRIC CO., LTD.','Nonferrous Metals'),
    ('5802.T','SUMITOMO ELECTRIC IND., LTD.','Nonferrous Metals'),('5803.T','FUJIKURA LTD.','Nonferrous Metals'),('2768.T','SOJITZ CORP.','Trading Companies'),
    ('8001.T','ITOCHU CORP.','Trading Companies'),('8002.T','MARUBENI CORP.','Trading Companies'),('8015.T','TOYOTA TSUSHO CORP.','Trading Companies'),
    ('8031.T','MITSUI & CO., LTD.','Trading Companies'),('8053.T','SUMITOMO CORP.','Trading Companies'),('8058.T','MITSUBISHI CORP.','Trading Companies'),
    ('1721.T','COMSYS HOLDINGS CORP.','Construction'),('1801.T','TAISEI CORP.','Construction'),('1802.T','OBAYASHI CORP.','Construction'),
    ('1803.T','SHIMIZU CORP.','Construction'),('1808.T','HASEKO CORP.','Construction'),('1812.T','KAJIMA CORP.','Construction'),
    ('1925.T','DAIWA HOUSE IND. CO., LTD.','Construction'),('1928.T','SEKISUI HOUSE, LTD.','Construction'),('1963.T','JGC HOLDINGS CORP.','Construction'),
    ('5631.T','THE JAPAN STEEL WORKS, LTD.','Machinery'),('6103.T','OKUMA CORP.','Machinery'),('6113.T','AMADA CO., LTD.','Machinery'),
    ('6273.T','SMC CORP.','Machinery'),('6301.T','KOMATSU LTD.','Machinery'),('6302.T','SUMITOMO HEAVY IND., LTD.','Machinery'),
    ('6305.T','HITACHI CONST. MACH. CO., LTD.','Machinery'),('6326.T','KUBOTA CORP.','Machinery'),('6361.T','EBARA CORP.','Machinery'),
    ('6367.T','DAIKIN INDUSTRIES, LTD.','Machinery'),('6471.T','NSK LTD.','Machinery'),('6472.T','NTN CORP.','Machinery'),
    ('6473.T','JTEKT CORP.','Machinery'),('7011.T','MITSUBISHI HEAVY IND., LTD.','Machinery'),('7013.T','IHI CORP.','Machinery'),
    ('7012.T','KAWASAKI HEAVY IND., LTD.','Shipbuilding'),('7832.T','BANDAI NAMCO HOLDINGS INC.','Other Manufacturing'),('7911.T','TOPPAN HOLDINGS INC.','Other Manufacturing'),
    ('7912.T','DAI NIPPON PRINTING CO., LTD.','Other Manufacturing'),('7951.T','YAMAHA CORP.','Other Manufacturing'),('3289.T','TOKYU FUDOSAN HOLDINGS CORP.','Real Estate'),
    ('8801.T','MITSUI FUDOSAN CO., LTD.','Real Estate'),('8802.T','MITSUBISHI ESTATE CO., LTD.','Real Estate'),('8804.T','TOKYO TATEMONO CO., LTD.','Real Estate'),
    ('8830.T','SUMITOMO REALTY & DEVELOPMENT CO., LTD.','Real Estate'),('9001.T','TOBU RAILWAY CO., LTD.','Railway & Bus'),('9005.T','TOKYU CORP.','Railway & Bus'),
    ('9007.T','ODAKYU ELECTRIC RAILWAY CO., LTD.','Railway & Bus'),('9008.T','KEIO CORP.','Railway & Bus'),('9009.T','KEISEI ELECTRIC RAILWAY CO., LTD.','Railway & Bus'),
    ('9020.T','EAST JAPAN RAILWAY CO.','Railway & Bus'),('9021.T','WEST JAPAN RAILWAY CO.','Railway & Bus'),('9022.T','CENTRAL JAPAN RAILWAY CO., LTD.','Railway & Bus'),
    ('9064.T','YAMATO HOLDINGS CO., LTD.','Land Transport'),('9147.T','NIPPON EXPRESS HOLDINGS, INC.','Land Transport'),('9101.T','NIPPON YUSEN K.K.','Marine Transport'),
    ('9104.T','MITSUI O.S.K.LINES, LTD.','Marine Transport'),('9107.T','KAWASAKI KISEN KAISHA, LTD.','Marine Transport'),('9201.T','JAPAN AIRLINES CO., LTD.','Air Transport'),
    ('9202.T','ANA HOLDINGS INC.','Air Transport'),('9501.T','TOKYO ELECTRIC POWER COMPANY HOLDINGS, I','Electric Power'),('9502.T','CHUBU ELECTRIC POWER CO., INC.','Electric Power'),
    ('9503.T','THE KANSAI ELECTRIC POWER CO., INC.','Electric Power'),('9531.T','TOKYO GAS CO., LTD.','Gas'),('9532.T','OSAKA GAS CO., LTD.','Gas'),
]

_KOSPI = [
    ('090430.KS','Amorepacific','Consumer Staples'),('002790.KS','Amorepacific Holdings','Consumer Staples'),('278470.KS','APR','Consumer Staples'),
    ('002030.KS','Asia Holdings','Steels & Materials'),('282330.KS','BGF Retail','Consumer Staples'),('138930.KS','BNK Financial','Financials'),
    ('068270.KS','Celltrion','Health Care'),('030000.KS','Cheil Worldwide','Communication Services'),('185750.KS','Chong Kun Dang','Health Care'),
    ('001040.KS','CJ','Consumer Staples'),('097950.KS','CJ CheilJedang','Consumer Staples'),('000120.KS','CJ Logistics','Industrials'),
    ('192820.KS','Cosmax','Consumer Staples'),('005420.KS','Cosmo Chemical','Energy & Chemicals'),('021240.KS','Coway','Consumer Discretionary'),
    ('112610.KS','CS Wind','Heavy Industries'),('483650.KS',"d'Alba Global",'Consumer Staples'),('001680.KS','Daesang','Consumer Staples'),
    ('047040.KS','Daewoo E&C','Constructions'),('003090.KS','Daewoong','Health Care'),('069620.KS','Daewoong Pharmaceutical','Health Care'),
    ('000990.KS','DB HiTek','IT'),('005830.KS','DB Insurance','Financials'),('000210.KS','DL','Constructions'),
    ('375500.KS','DL E&C','Constructions'),('007340.KS','DN Automotive','Consumer Discretionary'),('026960.KS','Dongsuh','Consumer Staples'),
    ('006040.KS','Dongwon Industries','Consumer Staples'),('014820.KS','Dongwon Systems','Steels & Materials'),('000150.KS','Doosan','Heavy Industries'),
    ('241560.KS','Doosan Bobcat','Heavy Industries'),('034020.KS','Doosan Enerbility','Heavy Industries'),('454910.KS','Doosan Robotics','Heavy Industries'),
    ('192080.KS','DoubleU Games','Consumer Discretionary'),('450080.KS','Ecopro Materials','Industrials'),('139480.KS','Emart','Consumer Staples'),
    ('383220.KS','F&F','Consumer Discretionary'),('093370.KS','Foosung','Energy & Chemicals'),('006280.KS','Green Cross','Health Care'),
    ('078930.KS','GS','Energy & Chemicals'),('007070.KS','GS Retail','Consumer Staples'),('086790.KS','Hana Financial','Financials'),
    ('009420.KS','Hanall Biopharma','Health Care'),('300720.KS','Hanil Cement','Constructions'),('180640.KS','Hanjin KAL','Consumer Discretionary'),
    ('161390.KS','Hankook','Consumer Discretionary'),('000240.KS','Hankook & Company','Consumer Discretionary'),('128940.KS','Hanmi Pharm','Health Care'),
    ('008930.KS','Hanmi Science','Health Care'),('042700.KS','Hanmi Semiconductor','IT'),('018880.KS','Hanon Systems','Consumer Discretionary'),
    ('014680.KS','Hansol Chemical','Energy & Chemicals'),('009240.KS','Hanssem','Consumer Discretionary'),('000880.KS','Hanwha','Energy & Chemicals'),
    ('012450.KS','Hanwha Aerospace','Industrials'),('082740.KS','Hanwha Engine','Heavy Industries'),('088350.KS','Hanwha Life','Financials'),
    ('042660.KS','Hanwha Ocean','Heavy Industries'),('009830.KS','Hanwha Solutions','Energy & Chemicals'),('272210.KS','Hanwha Systems','Industrials'),
    ('267270.KS','HD Construction Equipment','Heavy Industries'),('267250.KS','HD Hyundai','Energy & Chemicals'),('267260.KS','HD Hyundai Electric','Heavy Industries'),
    ('329180.KS','HD Hyundai Heavy Industries','Heavy Industries'),('071970.KS','HD Hyundai Marine Engine','Heavy Industries'),('443060.KS','HD Hyundai Marine Solution','Industrials'),
    ('009540.KS','HD KSOE','Heavy Industries'),('017960.KS','Hankuk Carbon','Energy & Chemicals'),('000080.KS','HiteJinro','Consumer Staples'),
    ('204320.KS','HL Mando','Consumer Discretionary'),('011200.KS','HMM','Industrials'),('008770.KS','Hotel Shilla','Consumer Discretionary'),
    ('298050.KS','HS Hyosung Advanced Materials','Energy & Chemicals'),('352820.KS','Hybe','Communication Services'),('298040.KS','Hyosung Heavy Industries','Heavy Industries'),
    ('298020.KS','Hyosung TNC','Energy & Chemicals'),('307950.KS','Hyundai AutoEver','IT'),('069960.KS','Hyundai Department Store','Consumer Discretionary'),
    ('000720.KS','Hyundai E&C','Constructions'),('017800.KS','Hyundai Elevator','Heavy Industries'),('086280.KS','Hyundai Glovis','Industrials'),
    ('001450.KS','Hyundai Marine & Fire','Financials'),('012330.KS','Hyundai Mobis','Consumer Discretionary'),('005380.KS','Hyundai Motor','Consumer Discretionary'),
    ('064350.KS','Hyundai Rotem','Heavy Industries'),('004020.KS','Hyundai Steel','Steels & Materials'),('011210.KS','Hyundai WIA','Consumer Discretionary'),
    ('139130.KS','IM Financial','Financials'),('024110.KS','Industrial Bank of Korea','Financials'),('007660.KS','Isu Petasys','IT'),
    ('457190.KS','Isu Specialty Chemical','Energy & Chemicals'),('175330.KS','JB Financial','Financials'),('035720.KS','Kakao','Communication Services'),
    ('323410.KS','KakaoBank','Financials'),('377300.KS','KakaoPay','Financials'),('035250.KS','Kangwon Land','Consumer Discretionary'),
    ('105560.KS','KB Financial','Financials'),('002380.KS','KCC','Constructions'),('015760.KS','KEPCO','Consumer Staples'),
    ('052690.KS','KEPCO E&C','Constructions'),('051600.KS','KEPCO KPS','Constructions'),('000270.KS','Kia','Consumer Discretionary'),
    ('039490.KS','Kiwoom Securities','Financials'),('161890.KS','Kolmar Korea','Consumer Staples'),('120110.KS','Kolon Industries','Energy & Chemicals'),
    ('047810.KS','Korea Aerospace','Industrials'),('071320.KS','Korea District Heating','Consumer Staples'),('036460.KS','Korea Gas','Consumer Staples'),
    ('071050.KS','Korea Investment','Financials'),('006650.KS','Korea Petrochemical','Energy & Chemicals'),('010130.KS','Korea Zinc','Steels & Materials'),
    ('003490.KS','Korean Air','Industrials'),('259960.KS','Krafton','Communication Services'),('030200.KS','KT','Communication Services'),
    ('033780.KS','KT&G','Consumer Staples'),('011780.KS','Kumho Petrochemical','Energy & Chemicals'),('073240.KS','Kumho Tire','Consumer Discretionary'),
    ('066970.KS','L&F','Industrials'),('003550.KS','LG','IT'),('051910.KS','LG Chem','Energy & Chemicals'),
    ('064400.KS','LG CNS','IT'),('034220.KS','LG Display','IT'),('066570.KS','LG Electronics','IT'),
    ('373220.KS','LG Energy Solution','Industrials'),('051900.KS','LG H&H','Consumer Staples'),('011070.KS','LG Innotek','IT'),
    ('032640.KS','LG Uplus','Communication Services'),('079550.KS','LIG Nex1','Industrials'),('004990.KS','Lotte','Consumer Staples'),
    ('011170.KS','Lotte Chemical','Energy & Chemicals'),('005300.KS','Lotte Chilsung','Consumer Staples'),('004000.KS','Lotte Fine Chemical','Energy & Chemicals'),
    ('023530.KS','Lotte Shopping','Consumer Discretionary'),('280360.KS','Lotte Wellfood','Consumer Staples'),('006260.KS','LS','Industrials'),
    ('010120.KS','LS Electric','Industrials'),('138040.KS','Meritz Financial','Financials'),('006800.KS','Mirae Asset Securities','Financials'),
    ('081660.KS','Misto','Consumer Discretionary'),('002840.KS','Miwon Commercial','Energy & Chemicals'),('268280.KS','Miwon Specialty Chemical','Energy & Chemicals'),
    ('035420.KS','Naver','Communication Services'),('036570.KS','NC','Communication Services'),('251270.KS','Netmarble','Communication Services'),
    ('005940.KS','NH Investment & Securities','Financials'),('004370.KS','Nongshim','Consumer Staples'),('456040.KS','OCI','Energy & Chemicals'),
    ('010060.KS','OCI Holdings','Energy & Chemicals'),('271560.KS','Orion','Consumer Staples'),('001800.KS','Orion Holdings','Consumer Staples'),
    ('007310.KS','Ottogi','Consumer Staples'),('028670.KS','Pan Ocean','Industrials'),('034230.KS','Paradise','Consumer Discretionary'),
    ('103140.KS','Poongsan','Steels & Materials'),('005490.KS','POSCO','Steels & Materials'),('022100.KS','POSCO DX','IT'),
    ('003670.KS','POSCO Future M','Industrials'),('047050.KS','POSCO International','Industrials'),('012750.KS','S-1','Industrials'),
    ('062040.KS','Sanil Electric','Heavy Industries'),('207940.KS','Samsung Biologics','Health Care'),('028260.KS','Samsung C&T','Constructions'),
    ('029780.KS','Samsung Card','Financials'),('028050.KS','Samsung E&A','Constructions'),('009150.KS','Samsung Electro-Mechanics','IT'),
    ('005930.KS','Samsung Electronics','IT'),('0126Z0.KS','Samsung Epis','Health Care'),('000810.KS','Samsung Fire & Marine','Financials'),
    ('010140.KS','Samsung Heavy Industries','Heavy Industries'),('032830.KS','Samsung Life','Financials'),('006400.KS','Samsung SDI','IT'),
    ('018260.KS','Samsung SDS','IT'),('016360.KS','Samsung Securities','Financials'),('003230.KS','Samyang Foods','Consumer Staples'),
    ('137310.KS','SD Biosensor','Health Care'),('001430.KS','Seah Besteel','Steels & Materials'),('003030.KS','Seah Steel Holdings','Steels & Materials'),
    ('055550.KS','Shinhan Financial','Financials'),('004170.KS','Shinsegae','Consumer Discretionary'),('034730.KS','SK','Energy & Chemicals'),
    ('326030.KS','SK Biopharm','Health Care'),('302440.KS','SK Bioscience','Health Care'),('285130.KS','SK Chemicals','Energy & Chemicals'),
    ('000660.KS','SK Hynix','IT'),('361610.KS','SK IE Technology','Industrials'),('096770.KS','SK Innovation','Energy & Chemicals'),
    ('402340.KS','SK Square','IT'),('017670.KS','SK Telecom','Communication Services'),('011790.KS','SKC','Energy & Chemicals'),
    ('005850.KS','SL','Consumer Discretionary'),('010950.KS','S-Oil','Energy & Chemicals'),('003240.KS','Taekwang Industrial','Energy & Chemicals'),
    ('001440.KS','Taihan Cable & Solution','Industrials'),('069260.KS','TKG Huchems','Energy & Chemicals'),('316140.KS','Woori Financial','Financials'),
    ('008730.KS','Youlchon Chemical','Steels & Materials'),('000670.KS','Young Poong','Steels & Materials'),('111770.KS','Youngone','Consumer Discretionary'),
    ('009970.KS','Youngone Holdings','Consumer Discretionary'),('000100.KS','Yuhan','Health Care'),
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
