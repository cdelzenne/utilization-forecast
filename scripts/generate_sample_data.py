"""Generate the synthetic APAC staffing and pipeline sample data used by the dashboard.

Every name, client and figure is invented. Run from the repository root:

    python3 scripts/generate_sample_data.py

Writes data/apac_staffing_forecast.csv (one row per person per week) and
data/apac_pipeline.csv (open opportunities). The fixed seed makes the output reproducible.
"""
import os
import random, csv, datetime as dt
random.seed(55)

WEEKS = [dt.date(2026, 11, 16) + dt.timedelta(weeks=i) for i in range(8)]
OFFICES = {
    "fifty-five": ["Hong Kong", "Shanghai", "Shenzhen", "Singapore"],
    "Jellyfish": ["Singapore", "Bangkok", "Jakarta", "Seoul", "Tokyo", "Hong Kong", "Shanghai"],
}
HEAD = {("fifty-five","Hong Kong"):22,("fifty-five","Shanghai"):20,("fifty-five","Shenzhen"):12,("fifty-five","Singapore"):14,
        ("Jellyfish","Singapore"):16,("Jellyfish","Bangkok"):10,("Jellyfish","Jakarta"):9,("Jellyfish","Seoul"):8,
        ("Jellyfish","Tokyo"):11,("Jellyfish","Hong Kong"):7,("Jellyfish","Shanghai"):8}
TITLES = {  # title: (weight, target util, family)
 "Consultant":(10,.85,"consult"),"Senior Consultant":(8,.82,"consult"),"Project Lead":(5,.75,"consult"),
 "Consulting Manager":(4,.65,"consult"),"Measurement Specialist":(6,.85,"measure"),"Sr Measurement Specialist":(4,.80,"measure"),
 "Cloud Specialist":(5,.85,"cloud"),"Sr Cloud Specialist":(3,.80,"cloud"),"Data Eng":(7,.88,"eng"),"Sr Data Eng":(4,.82,"eng"),
 "Data Scientist":(5,.85,"ds"),"Sr Data Scientist":(3,.80,"ds"),"Data Architect":(3,.80,"eng"),"Sr Data Architect":(2,.75,"eng")}
CERTS_BY_FAMILY = {
 "consult":["Google Marketing Platform","Adobe","Salesforce","Contentsquare","AB Tasty","Didomi","OneTrust","Piano"],
 "measure":["Google Marketing Platform","Adobe","Piano","Commanders Act","Piwik PRO","Contentsquare","LiveRamp","Didomi"],
 "cloud":["Google Cloud","AWS","Azure","Power BI","Google Marketing Platform"],
 "eng":["Google Cloud","AWS","Azure","Power BI","Salesforce","LiveRamp","Commanders Act"],
 "ds":["Google Cloud","AWS","Azure","Power BI","Google Marketing Platform"],
}
# public holidays affecting capacity (days off) per office per week index
HOL = {"Singapore":{6:1,7:1},"Hong Kong":{5:2,6:1,7:1},"Shanghai":{6:1,7:1},"Shenzhen":{6:1,7:1},
       "Bangkok":{3:1,5:1,6:1,7:1},"Jakarta":{5:1,6:1,7:1},"Seoul":{5:1,6:1,7:1},"Tokyo":{1:1,6:2,7:2}}
FIRST=["Wei","Mei","Jun","Ka Ho","Wing","Yan","Hao","Li","Siti","Arif","Dewi","Nattapong","Ploy","Somchai","Ji-woo","Min-jun","Seo-yeon",
 "Haruto","Yui","Ren","Aiko","Daniel","Priya","Rahul","Chloe","Marcus","Sarah","Kenji","Tan","Rachel","Eunice","Bryan","Ivy","Leo","Grace"]
LAST=["Chan","Wong","Li","Zhang","Liu","Tan","Lim","Ng","Santoso","Wijaya","Suwan","Chaiyaporn","Kim","Park","Lee","Sato","Tanaka","Suzuki",
 "Ho","Lau","Cheung","Chen","Huang","Yamamoto","Nakamura","Koh","Goh","Teo","Pratama","Rattana"]
CLIENTS=["Luxury maison A","Cosmetics group B","Telco C","Bank D","Insurer E","Auto OEM F","Retailer G","CPG H","Airline I","Hotel group J",
 "E-commerce K","Gaming L","Beverage M","Electronics N"]

title_list=list(TITLES); tw=[TITLES[t][0] for t in title_list]
people=[]; rows=[]; pipeline=[]
pid=0
for (bu,office),n in HEAD.items():
    for _ in range(n):
        pid+=1
        t=random.choices(title_list,tw)[0]
        fam=TITLES[t][2]
        pool=CERTS_BY_FAMILY[fam]
        k=random.choice([1,1,2,2,3])
        certs=sorted(random.sample(pool,min(k,len(pool))))
        if "Sr" in t or "Senior" in t or "Manager" in t or "Architect" in t:
            extra=[c for c in pool if c not in certs]
            if extra: certs=sorted(certs+[random.choice(extra)])
        name=f"{random.choice(FIRST)} {random.choice(LAST)}"
        people.append({"id":f"P{pid:03d}","name":name,"bu":bu,"office":office,"title":t,"target":TITLES[t][1],"certs":certs})

# office demand profile: some hot, some cold
OFFICE_HEAT={"Hong Kong":1.05,"Shanghai":0.97,"Shenzhen":0.88,"Singapore":1.08,"Bangkok":0.80,"Jakarta":0.92,"Seoul":1.00,"Tokyo":1.12}
CERT_HEAT={"Google Cloud":1.12,"Google Marketing Platform":1.06,"Salesforce":1.10,"AWS":0.95,"Azure":0.85,"Adobe":0.92,"LiveRamp":1.08,
 "Contentsquare":0.97,"Piano":0.9,"Commanders Act":0.88,"Piwik PRO":0.86,"Didomi":0.9,"OneTrust":0.93,"AB Tasty":0.9,"Power BI":0.96}

for p in people:
    heat=OFFICE_HEAT[p["office"]]*sum(CERT_HEAT[c] for c in p["certs"])/len(p["certs"])
    if p["bu"]=="Jellyfish": heat*=0.97
    base=min(1.0,max(0.15,random.gauss(p["target"]*heat,0.14)))
    clients=random.sample(CLIENTS,random.choice([1,2,2,3]))
    # confirmed project roll-off week for some
    rolloff=random.choice([None,None,None,2,3,4,5,6])
    leave_week=random.choice([None]*5+[4,5,6,7,7])
    for i,w in enumerate(WEEKS):
        hol=HOL[p["office"]].get(i,0)
        leave=0
        if leave_week is not None and i==leave_week: leave=random.choice([2,3,5])
        cap_days=max(0,5-hol-leave)
        cap=cap_days*8
        # booked decays across horizon (confirmed work), plus roll-off
        decay=max(0.35,1-0.075*i)
        b=base*decay
        if rolloff is not None and i>=rolloff: b*=0.45
        booked=round(min(cap*1.15,max(0,random.gauss(b*cap,2.5))),1)
        # pipeline weighted grows over horizon
        pip_raw=max(0,random.gauss((base*(1-decay)+0.05)*cap*1.6,3))
        prob=round(random.choice([0.25,0.4,0.5,0.6,0.75]),2)
        weighted=round(pip_raw*prob,1)
        if cap==0: booked=weighted=0; pip_raw=0
        rows.append({"person_id":p["id"],"week":w.isoformat(),"capacity_h":cap,"booked_h":booked,
                     "pipeline_unweighted_h":round(pip_raw,1),"pipeline_weighted_h":weighted,
                     "forecast_h":round(booked+weighted,1),"holiday_days":hol,"leave_days":leave,
                     "primary_client":clients[i%len(clients)]})

# pipeline opportunities (for a list)
STAGES=[("Proposal",0.5),("Shortlisted",0.6),("Verbal",0.75),("Qualified",0.25),("Scoping",0.4)]
OPPS=["MMM refresh (Meridian)","Server-side tagging migration","CDP composable build","GenAI product-feed enrichment","CAPI & consent mode rollout",
 "Clean-room analytics (ADH/AMC)","Data platform on GCP","Salesforce Data Cloud activation","CRO retainer","Data governance audit",
 "Contentsquare implementation","Agentic tracking pilot","Looker dashboards suite","Azure lakehouse build"]
for j in range(26):
    st,pr=random.choice(STAGES)
    bu=random.choice(["fifty-five","fifty-five","Jellyfish"])
    off=random.choice(OFFICES[bu])
    start=random.randint(0,6)
    ttl=random.sample(title_list,random.choice([2,3,4]))
    opp=random.choice(OPPS)
    need={"MMM":["Google Marketing Platform"],"GCP":["Google Cloud"],"Salesforce":["Salesforce"],"Azure":["Azure"],"Contentsquare":["Contentsquare"],
          "Clean-room":["LiveRamp","Google Marketing Platform"],"CAPI":["Google Marketing Platform","OneTrust"],"Looker":["Google Cloud"],"CDP":["Salesforce","Google Cloud"]}
    certs=[]
    for k,v in need.items():
        if k in opp: certs=v
    if not certs: certs=[random.choice(list(CERT_HEAT))]
    pipeline.append({"opp":opp,"client":random.choice(CLIENTS),"bu":bu,"office":off,"stage":st,"probability":pr,
                     "start_week":WEEKS[start].isoformat(),"weeks":random.choice([4,6,8,12]),
                     "fte":random.choice([1,1.5,2,2.5,3,4]),"titles":ttl,"certs":certs})


# ---- write flat CSVs consumed by the dashboard ----
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
os.makedirs(OUT, exist_ok=True)
by_id = {p["id"]: p for p in people}
flat = []
for r in rows:
    p = by_id[r["person_id"]]
    flat.append({"person_id": r["person_id"], "name": p["name"], "bu": p["bu"], "office": p["office"],
                 "title": p["title"], "certifications": "|".join(p["certs"]), "target_util": p["target"],
                 "week": r["week"], "capacity_h": r["capacity_h"], "booked_h": r["booked_h"],
                 "pipeline_weighted_h": r["pipeline_weighted_h"], "forecast_h": r["forecast_h"],
                 "holiday_days": r["holiday_days"], "leave_days": r["leave_days"]})
with open(os.path.join(OUT, "apac_staffing_forecast.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(flat[0])); w.writeheader(); w.writerows(flat)

opps = []
for i, o in enumerate(pipeline):
    opps.append({"id": f"OPP-{i + 1:03d}", "opp": o["opp"], "client": o["client"], "bu": o["bu"], "office": o["office"],
                 "stage": o["stage"], "probability": o["probability"], "start_week": o["start_week"], "weeks": o["weeks"],
                 "fte": o["fte"], "titles": "|".join(o["titles"]), "certs": "|".join(o["certs"])})
with open(os.path.join(OUT, "apac_pipeline.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(opps[0])); w.writeheader(); w.writerows(opps)

cap = sum(r["capacity_h"] for r in rows)
print(f"{len(people)} people, {len(rows)} person-weeks, {len(opps)} opportunities; "
      f"forecast utilization {100 * sum(r['forecast_h'] for r in rows) / cap:.1f}%")
