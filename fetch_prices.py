"""
Fetches latest stock prices for Saju's portfolio using yfinance (server-side, no CORS).
Run by GitHub Actions after market close. Saves results to prices.json.
"""
import yfinance as yf
import json
from datetime import datetime, timezone
import time

PORTFOLIO = [
    {"name": "AAA TECHNOLOGIES LIMITED",          "icici": "AAATEC", "nse": "AAATECH"},
    {"name": "ADD SHOP E RETAIL LIMITED",          "icici": "ADDPRO", "nse": "ADDICTIVE"},
    {"name": "INSPIRISYS SOLUTIONS LIMITED",       "icici": "AFL",    "nse": "INSPIRISYS"},
    {"name": "AGS TRANSACT TECHNOLOGIES LTD",      "icici": "AGSTRA", "nse": "AGSTRA"},
    {"name": "AJANTA SOYA LIMITED",                "icici": "AJASOY", "nse": "AJANTSOYA"},
    {"name": "AMBUJA CEMENTS LTD",                 "icici": "AMBCE",  "nse": "AMBUJACEM"},
    {"name": "ANUH PHARMA LTD",                    "icici": "ANUPHA", "nse": "ANUHPHR"},
    {"name": "ASIAN HOTELS (EAST) LIMITED",        "icici": "ASIEAS", "nse": "AHLEAST"},
    {"name": "ASI INDUSTRIES LIMITED",             "icici": "ASSSTO", "nse": "ASIIND"},
    {"name": "AVANTI FEEDS LTD",                   "icici": "AVAFEE", "nse": "AVANTIFEED"},
    {"name": "AXIS BANK LIMITED",                  "icici": "AXIBAN", "nse": "AXISBANK"},
    {"name": "BANK OF BARODA",                     "icici": "BANBAR", "nse": "BANKBARODA"},
    {"name": "BANAS FINANCE LIMITED",              "icici": "BANFIN", "nse": "BANAS"},
    {"name": "BERYL SECURITIES LTD",               "icici": "BERSEC", "nse": "BERYL"},
    {"name": "BHARAT ELECTRONICS LTD",             "icici": "BHAELE", "nse": "BEL"},
    {"name": "BHARAT HEAVY ELECTRICALS LTD",       "icici": "BHEL",   "nse": "BHEL"},
    {"name": "BODAL CHEMICALS LTD",                "icici": "BODCHE", "nse": "BODALCHEM"},
    {"name": "CALIFORNIA SOFTWARE CO LTD",         "icici": "CALSOF", "nse": "CALSOFT"},
    {"name": "COX AND KINGS FINANCIAL SER LTD",    "icici": "CNKFIN", "nse": "EZYINFRA"},
    {"name": "COX AND KINGS LIMITED",              "icici": "CNKLIM", "nse": "COX&KINGS"},
    {"name": "CPSE ETF",                           "icici": "CPSETF", "nse": "CPSEETF"},
    {"name": "DAVANGERE SUGAR COMPANY LTD",        "icici": "DAVSUG", "nse": "DAVANGERE"},
    {"name": "DELHIVERY LIMITED",                  "icici": "DELLIM", "nse": "DELHIVERY"},
    {"name": "DEVYANI INTERNATIONAL LIMITED",      "icici": "DEVIN",  "nse": "DEVYANI"},
    {"name": "DIVIS LABORATORIES LIMITED",         "icici": "DIVLAB", "nse": "DIVISLAB"},
    {"name": "DOLAT ALGOTECH LIMITED",             "icici": "DOLINV", "nse": "DOLATALGO"},
    {"name": "DPSC Limited",                       "icici": "DPSLIM", "nse": "DPSCLTD"},
    {"name": "EASY TRIP PLANNERS LIMITED",         "icici": "EASTRI", "nse": "EASEMYTRIP"},
    {"name": "EIH LIMITED",                        "icici": "EIHLIM", "nse": "EIHOTEL"},
    {"name": "ELECTROSTEEL CASTINGS LTD",          "icici": "ELECAS", "nse": "ELECTCAST"},
    {"name": "EXIDE INDUSTRIES LTD",               "icici": "EXIIND", "nse": "EXIDEIND"},
    {"name": "FCS SOFTWARE SOLUTIONS LIMITED",     "icici": "FCSSOF", "nse": "FCSSOFT"},
    {"name": "FILATEX FASHIONS LIMITED",           "icici": "FILFAS", "nse": "FILATFASH"},
    {"name": "FIRSTSOURCE SOLUTIONS LTD",          "icici": "FIRSOU", "nse": "FSL"},
    {"name": "FUTURE RETAIL LIMITED",              "icici": "FUTRE",  "nse": "FRETAIL"},
    {"name": "GENNEX LABORATORIES LIMITED",        "icici": "GENLAB", "nse": "GENNEX"},
    {"name": "GMR AIRPORTS LIMITED",               "icici": "GMRINF", "nse": "GMRAIRPORT"},
    {"name": "GMR POWER AND URBAN INFRA LTD",      "icici": "GMRPOW", "nse": "GMRP&UI"},
    {"name": "HCL INFOSYSTEMS LTD",                "icici": "HCLINF", "nse": "HCL-INSYS"},
    {"name": "HDFC BANK LIMITED",                  "icici": "HDFBAN", "nse": "HDFCBANK"},
    {"name": "HINDUSTAN CONSTRUCTION CO LTD",      "icici": "HINCON", "nse": "HCC"},
    {"name": "HINDUSTAN ZINC LTD",                 "icici": "HINZIN", "nse": "HINDZINC"},
    {"name": "ICICI BANK LIMITED",                 "icici": "ICIBAN", "nse": "ICICIBANK"},
    {"name": "ICICI PRUDENTIAL GOLD ETF",          "icici": "ICIGOL", "nse": "GOLDIETF"},
    {"name": "IGARASHI MOTORS INDIA LIMITED",      "icici": "IGAMOT", "nse": "IGARASHI"},
    {"name": "INDIA CEMENTS LTD",                  "icici": "INDCEM", "nse": "INDIACEM"},
    {"name": "INDIAN RAILWAY FIN CORP LTD",        "icici": "INDR",   "nse": "IRFC"},
    {"name": "AVENUESAI LIMITED",                  "icici": "INFINC", "nse": "AVENUESAI"},
    {"name": "JAIPRAKASH ASSOCIATES LIMITED",      "icici": "JAIASS", "nse": "JPASSOCIAT"},
    {"name": "JAIN IRRIGATION SYSTEMS LTD",        "icici": "JAIIRR", "nse": "JISLJALEQS"},
    {"name": "JAYASWAL NECO INDUSTRIES LTD",       "icici": "JAYNE",  "nse": "JAYNECOIND"},
    {"name": "JIO FINANCIAL SERVICES LIMITED",     "icici": "JIOFIN", "nse": "JIOFIN"},
    {"name": "JK TYRE AND INDUSTRIES LIMITED",     "icici": "JKTYRE", "nse": "JKTYRE"},
    {"name": "JUNIPER HOTELS LTD",                 "icici": "JUNHOT", "nse": "JUNIPER"},
    {"name": "KANSAI NEROLAC PAINTS",              "icici": "KANNER", "nse": "KANSAINER"},
    {"name": "KARNATAKA BANK LTD",                 "icici": "KARBAN", "nse": "KTKBANK"},
    {"name": "K C P SUGAR AND INDUSTRIES COR",     "icici": "KCPSUG", "nse": "KCPSUGIND"},
    {"name": "KITEX GARMENTS LTD",                 "icici": "KITGAR", "nse": "KITEX"},
    {"name": "K M SUGAR MILLS LTD",                "icici": "KMSUG",  "nse": "KMSUGAR"},
    {"name": "KOTHARI PETROCHEMICALS LIMITED",     "icici": "KOTPET", "nse": "KOTHARIPET"},
    {"name": "BIRLASOFT LIMITED",                  "icici": "KPITEC", "nse": "BSOFT"},
    {"name": "LANCOR HOLDINGS LIMITED",            "icici": "LANHOL", "nse": "LANCOR"},
    {"name": "LARSEN AND TOUBRO LIMITED",          "icici": "LARTOU", "nse": "LT"},
    {"name": "LE TRAVENUES TECHNOLOGY LTD",        "icici": "LETRA",  "nse": "IXIGO"},
    {"name": "LKP SECURITIES LIMITED",             "icici": "LKPSEC", "nse": "LKPSEC"},
    {"name": "MANGALAM GLOBAL ENTERPRISE LTD",     "icici": "MANGLO", "nse": "MANGLOBAL"},
    {"name": "MAYUR UNIQUOTERS LTD",               "icici": "MAYUNI", "nse": "MAYURUNIQ"},
    {"name": "UNO Minda Limited",                  "icici": "MININD", "nse": "UNOMINDA"},
    {"name": "MOONGIPA CAPITAL FINANCE LTD",       "icici": "MOOCAP", "nse": "MOONGIPAC"},
    {"name": "NETWORK 18 MEDIA & INVESTMENTS",     "icici": "NETW18", "nse": "NETWORK18"},
    {"name": "NHPC LIMITED",                       "icici": "NHPC",   "nse": "NHPC"},
    {"name": "NIRAJ CEMENT STRUCTURALS LIMITED",   "icici": "NICEME", "nse": "NIRAJ"},
    {"name": "ODYSSEY TECHNOLOGIES LTD",           "icici": "ODYTEC", "nse": "ODYSSEY"},
    {"name": "OLA ELECTRIC MOBILITY LIMITED",      "icici": "OLAELE", "nse": "OLAELEC"},
    {"name": "ONE 97 COMMUNICATIONS PAYTM",        "icici": "ONE97",  "nse": "PAYTM"},
    {"name": "ORIENTAL HOTELS LTD",                "icici": "ORIHOT", "nse": "ORIENTHOT"},
    {"name": "PANACEA BIOTEC LTD",                 "icici": "PANBIO", "nse": "PANACEABIO"},
    {"name": "PETRONET LNG LIMITED",               "icici": "PETLNG", "nse": "PETRONET"},
    {"name": "FAMILY CARE HOSPITALS LIMITED",      "icici": "PHAOFF", "nse": "FAMCARE"},
    {"name": "PCBL CHEMICAL LIMITED",              "icici": "PHICAR", "nse": "PCBL"},
    {"name": "PTC INDIA LIMITED",                  "icici": "POWTRA", "nse": "PTC"},
    {"name": "PRICOL LIMITED",                     "icici": "PRILI",  "nse": "PRICOLLTD"},
    {"name": "PTC INDIA FINANCIAL SERVICES LTD",   "icici": "PTCIND", "nse": "PFS"},
    {"name": "RAMKRISHNA FORGINGS LIMITED",        "icici": "RAMFOR", "nse": "RKFORGE"},
    {"name": "RATTANINDIA ENTERPRISES LTD",        "icici": "RATINF", "nse": "RTNINDIA"},
    {"name": "RAVINDER HEIGHTS LIMITED",           "icici": "RAVHEI", "nse": "RAVINDER"},
    {"name": "RELIANCE INDUSTRIES",                "icici": "RELIND", "nse": "RELIANCE"},
    {"name": "SARVESHWAR FOODS LTD",               "icici": "SARFOO", "nse": "SARVESHWAR"},
    {"name": "SBI CARDS AND PAYMENT SERV LTD",     "icici": "SBICAR", "nse": "SBICARD"},
    {"name": "SHALIMAR PRODUCTIONS LTD",           "icici": "SHAAGR", "nse": "SHALPROD"},
    {"name": "SHIVA CEMENT LTD",                   "icici": "SHICEM", "nse": "SHIVACEM"},
    {"name": "SINCLAIRS HOTELS LTD",               "icici": "SINHOT", "nse": "SINCHOTEL"},
    {"name": "SPEL SEMICONDUCTOR LIMITED",         "icici": "SPESEM", "nse": "SPELSEMI"},
    {"name": "STATE BANK OF INDIA",                "icici": "STABAN", "nse": "SBIN"},
    {"name": "TANEJA AEROSPACE & AVIATION LTD",    "icici": "TANAER", "nse": "TANEJA"},
    {"name": "TATA POWER CO LTD",                  "icici": "TATPOW", "nse": "TATAPOWER"},
    {"name": "TATA STEEL LIMITED",                 "icici": "TATSTE", "nse": "TATASTEEL"},
    {"name": "TATA CONSULTANCY SERVICES LTD",      "icici": "TCS",    "nse": "TCS"},
    {"name": "TEXMACO RAIL & ENGINEERING LIMITED", "icici": "TEXRAI", "nse": "TEXRAIL"},
    {"name": "TRIVENI GLASS LIMITED",              "icici": "TRIGLA", "nse": "TRIVENIGLAS"},
    {"name": "TRIDENT LTD",                        "icici": "TRILTD", "nse": "TRIDENT"},
    {"name": "TWINSTAR INDUSTRIES LIMITED",        "icici": "TWISOF", "nse": "TWINSTAR"},
    {"name": "UNION BANK OF INDIA",                "icici": "UNIBAN", "nse": "UNIONBANK"},
    {"name": "UNITED SPIRITS LIMITED",             "icici": "UNISPI", "nse": "MCDOWELL-N"},
    {"name": "VA TECH WABAG LIMITED",              "icici": "VATWAB", "nse": "WABAG"},
    {"name": "VIKAS LIFECARE LIMITED",             "icici": "VIKMUL", "nse": "VIKASLIFE"},
    {"name": "WEBSOL ENERGY SYSTEM LIMITED",       "icici": "WEBENE", "nse": "WEBELSOLAR"},
    {"name": "WELSPUN LIVING LIMITED",             "icici": "WELIND", "nse": "WELSPUNLIV"},
    {"name": "YES BANK LIMITED",                   "icici": "YESBAN", "nse": "YESBANK"},
    {"name": "ZEE ENTERTAINMENT ENTERPRISES",      "icici": "ZEEENT", "nse": "ZEEL"},
    {"name": "ZEE MEDIA CORPORATION LIMITED",      "icici": "ZEEMED", "nse": "ZEEMEDIA"},
    {"name": "ETERNAL LIMITED",                    "icici": "ZOMLIM", "nse": "ETERNAL"},
    {"name": "ZUARI AGRO CHEMICALS LIMITED",       "icici": "ZUAAGR", "nse": "ZUARI"},
]

def fetch_price(ticker_symbol):
    """Fetch price and prev close for a Yahoo Finance ticker symbol."""
    try:
        t = yf.Ticker(ticker_symbol)
        info = t.fast_info
        price = info.last_price
        prev_close = info.previous_close
        if price and float(price) > 0:
            exch = "NSE" if ticker_symbol.endswith(".NS") else "BSE"
            return {
                "price": round(float(price), 2),
                "prevClose": round(float(prev_close), 2) if prev_close else round(float(price), 2),
                "exchange": exch,
            }
    except Exception as e:
        pass
    return None

def main():
    snap = {}
    total = len(PORTFOLIO)
    ok = 0

    print(f"Fetching prices for {total} stocks...\n")

    for i, stock in enumerate(PORTFOLIO):
        icici = stock["icici"]
        nse   = stock["nse"]
        name  = stock["name"]

        result = None

        # Try NSE (.NS) first, then BSE (.BO), then ICICI code on BSE
        for sym in [nse + ".NS", nse + ".BO", icici + ".BO"]:
            result = fetch_price(sym)
            if result:
                break

        if result:
            snap[icici] = {
                "price":         result["price"],
                "prevClose":     result["prevClose"],
                "exchange":      result["exchange"],
                "lastTradeTime": int(datetime.now(timezone.utc).timestamp()),
                "marketState":   "CLOSED",
                "savedAt":       int(datetime.now(timezone.utc).timestamp() * 1000),
            }
            ok += 1
            print(f"[{i+1:>3}/{total}] ✓  {icici:<8}  {nse:<15}  ₹{result['price']:>10,.2f}  ({result['exchange']})")
        else:
            print(f"[{i+1:>3}/{total}] ✗  {icici:<8}  {nse:<15}  not found")

        # Small delay every 10 stocks to avoid Yahoo rate-limiting
        if (i + 1) % 10 == 0:
            time.sleep(1)

    now_utc = datetime.now(timezone.utc).isoformat()
    output = {
        "snap":    snap,
        "savedAt": now_utc,
        "source":  "github-actions",
    }

    with open("prices.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*55}")
    print(f"  Fetched {ok}/{total} stock prices")
    print(f"  Saved → prices.json  ({now_utc})")
    print(f"{'='*55}")

if __name__ == "__main__":
    main()
