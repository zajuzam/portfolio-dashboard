"""
Fetches latest stock prices for Saju's portfolio using yfinance (server-side, no CORS).
Run by GitHub Actions after market close. Saves results to prices.json.
Also fetches live MF NAVs from mfapi.in and inserts a daily portfolio snapshot
into PostgreSQL (Supabase / Neon / any Postgres) if DATABASE_URL is set.
"""
import os
import json
import time
import urllib.request
import psycopg2
from datetime import datetime, timezone, date
import yfinance as yf

# ---------------------------------------------------------------------------
# Stock holdings  (icici = ICICI Direct internal code, nse = Yahoo Finance
# base ticker without exchange suffix, qty = shares held)
# ---------------------------------------------------------------------------
PORTFOLIO = [
    {"name": "AAA TECHNOLOGIES LIMITED",          "icici": "AAATEC", "nse": "AAATECH",     "qty": 100},
    {"name": "ADD SHOP E RETAIL LIMITED",          "icici": "ADDPRO", "nse": "ASRL",        "qty": 101},
    {"name": "INSPIRISYS SOLUTIONS LIMITED",       "icici": "AFL",    "nse": "INSPIRISYS",  "qty": 100},
    {"name": "AGS TRANSACT TECHNOLOGIES LTD",      "icici": "AGSTRA", "nse": "AGSTRA",      "qty": 85},
    {"name": "AJANTA SOYA LIMITED",                "icici": "AJASOY", "nse": "AJANTSOY",    "qty": 2},
    {"name": "AMBUJA CEMENTS LTD",                 "icici": "AMBCE",  "nse": "AMBUJACEM",   "qty": 197},
    {"name": "ANUH PHARMA LTD",                    "icici": "ANUPHA", "nse": "ANUHPHR",     "qty": 100},
    {"name": "ASIAN HOTELS (EAST) LIMITED",        "icici": "ASIEAS", "nse": "AHLEAST",     "qty": 500},
    {"name": "ASI INDUSTRIES LIMITED",             "icici": "ASSSTO", "nse": "ASIIL",       "qty": 50},
    {"name": "AVANTI FEEDS LTD",                   "icici": "AVAFEE", "nse": "AVANTIFEED",  "qty": 100},
    {"name": "AXIS BANK LIMITED",                  "icici": "AXIBAN", "nse": "AXISBANK",    "qty": 36},
    {"name": "BANK OF BARODA",                     "icici": "BANBAR", "nse": "BANKBARODA",  "qty": 250},
    {"name": "BANAS FINANCE LIMITED",              "icici": "BANFIN", "nse": "BANASFN",     "qty": 1},
    {"name": "BERYL SECURITIES LTD",               "icici": "BERSEC", "nse": "BERYLSE",     "qty": 50},
    {"name": "BHARAT ELECTRONICS LTD",             "icici": "BHAELE", "nse": "BEL",         "qty": 190},
    {"name": "BHARAT HEAVY ELECTRICALS LTD",       "icici": "BHEL",   "nse": "BHEL",        "qty": 250},
    {"name": "BODAL CHEMICALS LTD",                "icici": "BODCHE", "nse": "BODALCHEM",   "qty": 20},
    {"name": "CALIFORNIA SOFTWARE CO LTD",         "icici": "CALSOF", "nse": "CALSOFT",     "qty": 1000},
    {"name": "COX AND KINGS FINANCIAL SER LTD",    "icici": "CNKFIN", "nse": "CKFSL",       "qty": 33},
    {"name": "COX AND KINGS LIMITED",              "icici": "CNKLIM", "nse": "COXKINGS",    "qty": 100},
    {"name": "CPSE ETF",                           "icici": "CPSETF", "nse": "CPSEETF",     "qty": 2500},
    {"name": "DAVANGERE SUGAR COMPANY LTD",        "icici": "DAVSUG", "nse": "DAVANGERE",   "qty": 500},
    {"name": "DELHIVERY LIMITED",                  "icici": "DELLIM", "nse": "DELHIVERY",   "qty": 10},
    {"name": "DEVYANI INTERNATIONAL LIMITED",      "icici": "DEVIN",  "nse": "DEVYANI",     "qty": 50},
    {"name": "DIVIS LABORATORIES LIMITED",         "icici": "DIVLAB", "nse": "DIVISLAB",    "qty": 12},
    {"name": "DOLAT ALGOTECH LIMITED",             "icici": "DOLINV", "nse": "DOLATALGO",   "qty": 2},
    {"name": "DPSC Limited",                       "icici": "DPSLIM", "nse": "DPSCLTD",     "qty": 100},
    {"name": "EASY TRIP PLANNERS LIMITED",         "icici": "EASTRI", "nse": "EASEMYTRIP",  "qty": 4000},
    {"name": "EIH LIMITED",                        "icici": "EIHLIM", "nse": "EIHOTEL",     "qty": 50},
    {"name": "ELECTROSTEEL CASTINGS LTD",          "icici": "ELECAS", "nse": "ELECTCAST",   "qty": 501},
    {"name": "EXIDE INDUSTRIES LTD",               "icici": "EXIIND", "nse": "EXIDEIND",    "qty": 40},
    {"name": "FCS SOFTWARE SOLUTIONS LIMITED",     "icici": "FCSSOF", "nse": "FCSSOFT",     "qty": 1000},
    {"name": "FILATEX FASHIONS LIMITED",           "icici": "FILFAS", "nse": "FILATFASH",   "qty": 1000},
    {"name": "FIRSTSOURCE SOLUTIONS LTD",          "icici": "FIRSOU", "nse": "FSL",         "qty": 100},
    {"name": "FUTURE RETAIL LIMITED",              "icici": "FUTRE",  "nse": "FRETAIL",     "qty": 500},
    {"name": "GENNEX LABORATORIES LIMITED",        "icici": "GENLAB", "nse": "GENNEX",      "qty": 9990},
    {"name": "GMR AIRPORTS LIMITED",               "icici": "GMRINF", "nse": "GMRAIRPORT",  "qty": 100},
    {"name": "GMR POWER AND URBAN INFRA LTD",      "icici": "GMRPOW", "nse": "GMRP&UI",     "qty": 10},
    {"name": "HCL INFOSYSTEMS LTD",                "icici": "HCLINF", "nse": "HCL-INSYS",   "qty": 1000},
    {"name": "HDFC BANK LIMITED",                  "icici": "HDFBAN", "nse": "HDFCBANK",    "qty": 50},
    {"name": "HINDUSTAN CONSTRUCTION CO LTD",      "icici": "HINCON", "nse": "HCC",         "qty": 260},
    {"name": "HINDUSTAN ZINC LTD",                 "icici": "HINZIN", "nse": "HINDZINC",    "qty": 30},
    {"name": "ICICI BANK LIMITED",                 "icici": "ICIBAN", "nse": "ICICIBANK",   "qty": 27},
    {"name": "ICICI PRUDENTIAL GOLD ETF",          "icici": "ICIGOL", "nse": "GOLDIETF",    "qty": 42},
    {"name": "IGARASHI MOTORS INDIA LIMITED",      "icici": "IGAMOT", "nse": "IGARASHI",    "qty": 42},
    {"name": "INDIA CEMENTS LTD",                  "icici": "INDCEM", "nse": "INDIACEM",    "qty": 50},
    {"name": "INDIAN RAILWAY FIN CORP LTD",        "icici": "INDR",   "nse": "IRFC",        "qty": 60},
    {"name": "AVENUESAI LIMITED",                  "icici": "INFINC", "nse": "CCAVENUE",    "qty": 400},
    {"name": "JAIPRAKASH ASSOCIATES LIMITED",      "icici": "JAIASS", "nse": "JPASSOCIAT",  "qty": 157},
    {"name": "JAIN IRRIGATION SYSTEMS LTD",        "icici": "JAIIRR", "nse": "JISLJALEQS",  "qty": 101},
    {"name": "JAYASWAL NECO INDUSTRIES LTD",       "icici": "JAYNE",  "nse": "JAYNECOIND",  "qty": 1},
    {"name": "JIO FINANCIAL SERVICES LIMITED",     "icici": "JIOFIN", "nse": "JIOFIN",      "qty": 65},
    {"name": "JK TYRE AND INDUSTRIES LIMITED",     "icici": "JKTYRE", "nse": "JKTYRE",      "qty": 620},
    {"name": "JUNIPER HOTELS LTD",                 "icici": "JUNHOT", "nse": "JUNIPER",     "qty": 40},
    {"name": "KANSAI NEROLAC PAINTS",              "icici": "KANNER", "nse": "KANSAINER",   "qty": 100},
    {"name": "KARNATAKA BANK LTD",                 "icici": "KARBAN", "nse": "KTKBANK",     "qty": 270},
    {"name": "K C P SUGAR AND INDUSTRIES COR",     "icici": "KCPSUG", "nse": "KCPSUGIND",   "qty": 100},
    {"name": "KITEX GARMENTS LTD",                 "icici": "KITGAR", "nse": "KITEX",       "qty": 543},
    {"name": "K M SUGAR MILLS LTD",                "icici": "KMSUG",  "nse": "KMSUGAR",     "qty": 50},
    {"name": "KOTHARI PETROCHEMICALS LIMITED",     "icici": "KOTPET", "nse": "KOTHARIPET",  "qty": 250},
    {"name": "BIRLASOFT LIMITED",                  "icici": "KPITEC", "nse": "BSOFT",       "qty": 50},
    {"name": "LANCOR HOLDINGS LIMITED",            "icici": "LANHOL", "nse": "LANCORHOL",   "qty": 50},
    {"name": "LARSEN AND TOUBRO LIMITED",          "icici": "LARTOU", "nse": "LT",          "qty": 18},
    {"name": "LE TRAVENUES TECHNOLOGY LTD",        "icici": "LETRA",  "nse": "IXIGO",       "qty": 50},
    {"name": "LKP SECURITIES LIMITED",             "icici": "LKPSEC", "nse": "LKPSEC",      "qty": 500},
    {"name": "MANGALAM GLOBAL ENTERPRISE LTD",     "icici": "MANGLO", "nse": "MGEL",        "qty": 2000},
    {"name": "MAYUR UNIQUOTERS LTD",               "icici": "MAYUNI", "nse": "MAYURUNIQ",   "qty": 71},
    {"name": "UNO Minda Limited",                  "icici": "MININD", "nse": "UNOMINDA",    "qty": 12},
    {"name": "MOONGIPA CAPITAL FINANCE LTD",       "icici": "MOOCAP", "nse": "MONGIPA",     "qty": 50},
    {"name": "NETWORK 18 MEDIA & INVESTMENTS",     "icici": "NETW18", "nse": "NETWORK18",   "qty": 116},
    {"name": "NHPC LIMITED",                       "icici": "NHPC",   "nse": "NHPC",        "qty": 101},
    {"name": "NIRAJ CEMENT STRUCTURALS LIMITED",   "icici": "NICEME", "nse": "NIRAJ",       "qty": 50},
    {"name": "ODYSSEY TECHNOLOGIES LTD",           "icici": "ODYTEC", "nse": "ODYSSEY",     "qty": 100},
    {"name": "OLA ELECTRIC MOBILITY LIMITED",      "icici": "OLAELE", "nse": "OLAELEC",     "qty": 50},
    {"name": "ONE 97 COMMUNICATIONS PAYTM",        "icici": "ONE97",  "nse": "PAYTM",       "qty": 6},
    {"name": "ORIENTAL HOTELS LTD",                "icici": "ORIHOT", "nse": "ORIENTHOT",   "qty": 164},
    {"name": "PANACEA BIOTEC LTD",                 "icici": "PANBIO", "nse": "PANACEABIO",  "qty": 1268},
    {"name": "PETRONET LNG LIMITED",               "icici": "PETLNG", "nse": "PETRONET",    "qty": 50},
    {"name": "FAMILY CARE HOSPITALS LIMITED",      "icici": "PHAOFF", "nse": "FAMILYCARE",  "qty": 1},
    {"name": "PCBL CHEMICAL LIMITED",              "icici": "PHICAR", "nse": "PCBL",        "qty": 421},
    {"name": "PTC INDIA LIMITED",                  "icici": "POWTRA", "nse": "PTC",         "qty": 200},
    {"name": "PRICOL LIMITED",                     "icici": "PRILI",  "nse": "PRICOLLTD",   "qty": 125},
    {"name": "PTC INDIA FINANCIAL SERVICES LTD",   "icici": "PTCIND", "nse": "PFS",         "qty": 100},
    {"name": "RAMKRISHNA FORGINGS LIMITED",        "icici": "RAMFOR", "nse": "RKFORGE",     "qty": 102},
    {"name": "RATTANINDIA ENTERPRISES LTD",        "icici": "RATINF", "nse": "RTNINDIA",    "qty": 51},
    {"name": "RAVINDER HEIGHTS LIMITED",           "icici": "RAVHEI", "nse": "RVHL",        "qty": 1268},
    {"name": "RELIANCE INDUSTRIES",                "icici": "RELIND", "nse": "RELIANCE",    "qty": 51},
    {"name": "SARVESHWAR FOODS LTD",               "icici": "SARFOO", "nse": "SARVESHWAR",  "qty": 800},
    {"name": "SBI CARDS AND PAYMENT SERV LTD",     "icici": "SBICAR", "nse": "SBICARD",     "qty": 24},
    {"name": "SHALIMAR PRODUCTIONS LTD",           "icici": "SHAAGR", "nse": "SHALPRO",     "qty": 2000},
    {"name": "SHIVA CEMENT LTD",                   "icici": "SHICEM", "nse": "SHIVACEM",    "qty": 200},
    {"name": "SINCLAIRS HOTELS LTD",               "icici": "SINHOT", "nse": "SINCLAIR",    "qty": 450},
    {"name": "SPEL SEMICONDUCTOR LIMITED",         "icici": "SPESEM", "nse": "SPELS",       "qty": 1050},
    {"name": "STATE BANK OF INDIA",                "icici": "STABAN", "nse": "SBIN",        "qty": 50},
    {"name": "TANEJA AEROSPACE & AVIATION LTD",    "icici": "TANAER", "nse": "TANAA",       "qty": 50},
    {"name": "TATA POWER CO LTD",                  "icici": "TATPOW", "nse": "TATAPOWER",   "qty": 225},
    {"name": "TATA STEEL LIMITED",                 "icici": "TATSTE", "nse": "TATASTEEL",   "qty": 286},
    {"name": "TATA CONSULTANCY SERVICES LTD",      "icici": "TCS",    "nse": "TCS",         "qty": 30},
    {"name": "TEXMACO RAIL & ENGINEERING LIMITED", "icici": "TEXRAI", "nse": "TEXRAIL",     "qty": 50},
    {"name": "TRIVENI GLASS LIMITED",              "icici": "TRIGLA", "nse": "TRIVENIGQ",   "qty": 2000},
    {"name": "TRIDENT LTD",                        "icici": "TRILTD", "nse": "TRIDENT",     "qty": 1},
    {"name": "TWINSTAR INDUSTRIES LIMITED",        "icici": "TWISOF", "nse": "TWINSTAR",    "qty": 10000},
    {"name": "UNION BANK OF INDIA",                "icici": "UNIBAN", "nse": "UNIONBANK",   "qty": 50},
    {"name": "UNITED SPIRITS LIMITED",             "icici": "UNISPI", "nse": "UNITDSPR",    "qty": 100},
    {"name": "VA TECH WABAG LIMITED",              "icici": "VATWAB", "nse": "WABAG",       "qty": 100},
    {"name": "VIKAS LIFECARE LIMITED",             "icici": "VIKMUL", "nse": "VIKASLIFE",   "qty": 500},
    {"name": "WEBSOL ENERGY SYSTEM LIMITED",       "icici": "WEBENE", "nse": "WEBELSOLAR",  "qty": 150},
    {"name": "WELSPUN LIVING LIMITED",             "icici": "WELIND", "nse": "WELSPUNLIV",  "qty": 20},
    {"name": "YES BANK LIMITED",                   "icici": "YESBAN", "nse": "YESBANK",     "qty": 600},
    {"name": "ZEE ENTERTAINMENT ENTERPRISES",      "icici": "ZEEENT", "nse": "ZEEL",        "qty": 50},
    {"name": "ZEE MEDIA CORPORATION LIMITED",      "icici": "ZEEMED", "nse": "ZEEMEDIA",    "qty": 100},
    {"name": "ETERNAL LIMITED",                    "icici": "ZOMLIM", "nse": "ETERNAL",     "qty": 71},
    {"name": "ZUARI AGRO CHEMICALS LIMITED",       "icici": "ZUAAGR", "nse": "ZUARI",       "qty": 100},
]

# ---------------------------------------------------------------------------
# Mutual Fund holdings  (schemeCode = AMFI code for mfapi.in)
# units = initialCurrent / initialNav  (kept in sync with dashboard)
# ---------------------------------------------------------------------------
MUTUAL_FUNDS = [
    {
        "name":       "ICICI Prudential Bluechip Fund - Growth",
        "schemeCode": "100355",
        "units":      615.39,   # 65634.94 / 106.66
        "fallbackNav": 106.66,
    },
    {
        "name":       "Nippon India Large Cap Fund - Growth",
        "schemeCode": "118269",
        "units":      1461.38,  # 129590.54 / 88.6707
        "fallbackNav": 88.6707,
    },
    {
        "name":       "ICICI Prudential Smallcap Fund - Growth",
        "schemeCode": "120828",
        "units":      3193.72,  # 270582.88 / 84.73
        "fallbackNav": 84.73,
    },
]


# ---------------------------------------------------------------------------
# Price fetcher
# ---------------------------------------------------------------------------
def fetch_price(ticker_symbol):
    """Fetch price and prev close for a Yahoo Finance ticker symbol.
    Tries fast_info first (liquid stocks). Falls back to history(period='5d')
    for illiquid/low-volume stocks where fast_info.last_price returns None.
    """
    exch = "NSE" if ticker_symbol.endswith(".NS") else "BSE"
    try:
        t = yf.Ticker(ticker_symbol)
        info = t.fast_info
        price = info.last_price
        prev_close = info.previous_close
        if price and float(price) > 0:
            return {
                "price":     round(float(price), 2),
                "prevClose": round(float(prev_close), 2) if prev_close else round(float(price), 2),
                "exchange":  exch,
            }
    except Exception:
        pass

    # Fallback: OHLC history for illiquid / thinly-traded stocks
    try:
        t = yf.Ticker(ticker_symbol)
        hist = t.history(period="5d")
        if not hist.empty:
            price = float(hist["Close"].iloc[-1])
            prev_close = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else price
            if price > 0:
                return {
                    "price":     round(price, 2),
                    "prevClose": round(prev_close, 2),
                    "exchange":  exch,
                }
    except Exception:
        pass

    return None


# ---------------------------------------------------------------------------
# Live NAV fetcher from mfapi.in  (free, no key needed)
# ---------------------------------------------------------------------------
def fetch_nav(scheme_code):
    """Returns latest NAV float for a given AMFI scheme code, or None."""
    try:
        url = f"https://api.mfapi.in/mf/{scheme_code}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        nav_str = data["data"][0]["nav"]   # most recent NAV is index 0
        return round(float(nav_str), 4)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Postgres snapshot insert
# ---------------------------------------------------------------------------
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS portfolio_snapshot (
    id            SERIAL PRIMARY KEY,
    snapshot_date DATE        NOT NULL,
    stocks_value  NUMERIC(14,2),
    mf_value      NUMERIC(14,2),
    total_value   NUMERIC(14,2),
    stocks_count  INT,
    created_at    TIMESTAMP   DEFAULT NOW(),
    UNIQUE (snapshot_date)
);
"""

def insert_snapshot(stocks_value, mf_value, stocks_count):
    """Insert (or update) today's portfolio snapshot into Postgres."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("  DATABASE_URL not set — skipping DB insert.")
        return

    total_value = stocks_value + mf_value
    today = date.today()

    try:
        conn = psycopg2.connect(db_url)
        cur  = conn.cursor()

        # Create table on first run
        cur.execute(CREATE_TABLE_SQL)

        # Upsert: if workflow runs twice on the same day, just overwrite
        cur.execute("""
            INSERT INTO portfolio_snapshot
                (snapshot_date, stocks_value, mf_value, total_value, stocks_count)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (snapshot_date) DO UPDATE SET
                stocks_value  = EXCLUDED.stocks_value,
                mf_value      = EXCLUDED.mf_value,
                total_value   = EXCLUDED.total_value,
                stocks_count  = EXCLUDED.stocks_count,
                created_at    = NOW()
        """, (today, round(stocks_value, 2), round(mf_value, 2),
              round(total_value, 2), stocks_count))

        conn.commit()
        cur.close()
        conn.close()
        print(f"  ✓ DB snapshot saved  →  date={today}  "
              f"stocks=₹{stocks_value:,.0f}  mf=₹{mf_value:,.0f}  "
              f"total=₹{total_value:,.0f}")
    except Exception as e:
        print(f"  ✗ DB insert failed: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    snap = {}
    total = len(PORTFOLIO)
    ok = 0

    print(f"Fetching prices for {total} stocks...\n")

    for i, stock in enumerate(PORTFOLIO):
        icici = stock["icici"]
        nse   = stock["nse"]

        result = None
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
            print(f"[{i+1:>3}/{total}] ✓  {icici:<8}  {nse:<15}  "
                  f"₹{result['price']:>10,.2f}  ({result['exchange']})")
        else:
            print(f"[{i+1:>3}/{total}] ✗  {icici:<8}  {nse:<15}  not found")

        if (i + 1) % 10 == 0:
            time.sleep(1)

    # --- Write prices.json ---
    now_utc = datetime.now(timezone.utc).isoformat()
    output = {"snap": snap, "savedAt": now_utc, "source": "github-actions"}
    with open("prices.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*55}")
    print(f"  Fetched {ok}/{total} stock prices")
    print(f"  Saved → prices.json  ({now_utc})")

    # --- Compute stocks total ---
    qty_map = {s["icici"]: s["qty"] for s in PORTFOLIO}
    stocks_value = sum(
        snap[code]["price"] * qty_map[code]
        for code in snap if code in qty_map
    )
    print(f"\n  Stocks value  : ₹{stocks_value:>14,.2f}  ({ok} priced)")

    # --- Fetch live MF NAVs and compute MF total ---
    print("\nFetching MF NAVs from mfapi.in...")
    mf_value = 0.0
    for mf in MUTUAL_FUNDS:
        nav = fetch_nav(mf["schemeCode"])
        if nav:
            current = nav * mf["units"]
            print(f"  ✓  {mf['name'][:45]:<45}  NAV ₹{nav}  →  ₹{current:,.0f}")
        else:
            current = mf["fallbackNav"] * mf["units"]
            print(f"  ✗  {mf['name'][:45]:<45}  using fallback NAV  →  ₹{current:,.0f}")
        mf_value += current

    print(f"\n  MF value      : ₹{mf_value:>14,.2f}")
    print(f"  Combined total: ₹{stocks_value + mf_value:>14,.2f}")
    print(f"{'='*55}")

    # --- Insert snapshot into Postgres ---
    print("\nInserting snapshot into PostgreSQL...")
    insert_snapshot(stocks_value, mf_value, ok)


if __name__ == "__main__":
    main()
