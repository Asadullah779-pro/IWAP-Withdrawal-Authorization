"""Executable policy reference model, not a production cryptocurrency signer.
Ed25519 authenticates synthetic intent/attestation records. SQLite serializes
reservations. No MPC, hardware quote, blockchain node, or deployed exchange.
"""
from __future__ import annotations
import copy, csv, hashlib, json, os, platform, random, sqlite3, statistics, tempfile, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'results'; OUT.mkdir(exist_ok=True)
NOW=1000
FIELDS=('id','customer','wallet','chain','asset','recipient','amount','fee_max','nonce','operation','epoch','expires')
def enc(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def digest(x): return hashlib.sha256(enc(x)).hexdigest()
class Issuer:
 def __init__(self): self.key=Ed25519PrivateKey.generate(); self.pub=self.key.public_key()
 def sign(self,x): return (copy.deepcopy(x), self.key.sign(enc(x)))
 def verify(self,x,s):
  try: self.pub.verify(s,enc(x)); return True
  except (InvalidSignature,ValueError,TypeError): return False
class Monitor:
 def __init__(self,ia,aa,cap=100000,omit=(),path=':memory:'):
  self.ia=ia; self.aa=aa; self.omit=set(omit); self.path=path
  self.db=sqlite3.connect(path,check_same_thread=False,timeout=30,isolation_level=None)
  self.db.executescript('CREATE TABLE IF NOT EXISTS budget(id INTEGER PRIMARY KEY, spent INTEGER); INSERT OR IGNORE INTO budget VALUES(1,0); CREATE TABLE IF NOT EXISTS consumed(id TEXT PRIMARY KEY, hash TEXT, amount INTEGER);')
  self.cap=cap
 def check(self,tx,cert,att,now=NOW):
  intent,sig=cert; evidence,esig=att
  if not self.ia.verify(intent,sig): return False,'intent_signature'
  if 'binding' not in self.omit and any(tx.get(k)!=intent.get(k) for k in FIELDS): return False,'binding'
  if 'operation' not in self.omit and tx.get('operation')!='transfer': return False,'operation'
  if 'epoch' not in self.omit and tx.get('epoch')!=1: return False,'epoch'
  if not isinstance(tx.get('amount'),int) or isinstance(tx['amount'],bool) or tx['amount']<=0: return False,'amount'
  if not isinstance(tx.get('fee_max'),int) or tx['fee_max']<0: return False,'fee'
  if 'expiry' not in self.omit and tx.get('expires',0)<=now: return False,'expiry'
  if not self.aa.verify(evidence,esig): return False,'attestation_signature'
  if 'attestation' not in self.omit:
   if evidence.get('request_hash')!=digest(tx) or evidence.get('workload')!='withdrawal-v1' or evidence.get('measurement')!='approved-build' or evidence.get('epoch')!=1 or not 0<=now-evidence.get('issued',0)<=30: return False,'attestation'
  try:
   self.db.execute('BEGIN IMMEDIATE')
   if 'replay' not in self.omit and self.db.execute('SELECT 1 FROM consumed WHERE id=?',(tx['id'],)).fetchone():
    self.db.execute('ROLLBACK'); return False,'replay'
   spent=self.db.execute('SELECT spent FROM budget WHERE id=1').fetchone()[0]
   charge=tx['amount']+tx['fee_max']
   if 'budget' not in self.omit and spent+charge>self.cap:
    self.db.execute('ROLLBACK'); return False,'budget'
   if 'replay' not in self.omit: self.db.execute('INSERT INTO consumed VALUES(?,?,?)',(tx['id'],digest(tx),charge))
   self.db.execute('UPDATE budget SET spent=spent+? WHERE id=1',(charge,)); self.db.execute('COMMIT')
   return True,'accepted'
  except Exception:
   if self.db.in_transaction: self.db.execute('ROLLBACK')
   raise
 def close(self): self.db.close()
def tx_for(i,amount=10,chain='EVM'):
 return dict(id=str(i),customer='c1',wallet='w1',chain=chain,asset='UNIT',recipient='recipient-1',amount=amount,fee_max=1,nonce=i,operation='transfer',epoch=1,expires=1060)
def attest(aa,tx,**kw):
 x=dict(request_hash=digest(tx),workload='withdrawal-v1',measurement='approved-build',epoch=1,issued=NOW); x.update(kw); return aa.sign(x)
def attack_cases():
 ia,aa=Issuer(),Issuer(); rows=[]
 kinds=['recipient_substitution','amount_increase','chain_substitution','delegation_disguise','forged_intent','duplicate_execution','expired_intent','old_policy_epoch','stale_attestation','attestation_other_request','unapproved_measurement','excess_budget']
 for kind in kinds:
  for seed in range(100):
   rng=random.Random(seed); tx=tx_for(seed, rng.randint(2,50)); intent=copy.deepcopy(tx); cert=ia.sign(intent); mon=Monitor(ia,aa,cap=1000)
   if kind=='recipient_substitution': tx['recipient']='attacker'
   elif kind=='amount_increase': tx['amount']+=100
   elif kind=='chain_substitution': tx['chain']='UTXO'
   elif kind=='delegation_disguise': tx['operation']='delegate'
   elif kind=='forged_intent': cert=Issuer().sign(intent)
   elif kind=='duplicate_execution': assert mon.check(tx,cert,attest(aa,tx))[0]
   elif kind=='expired_intent': tx['expires']=999; cert=ia.sign(tx)
   elif kind=='old_policy_epoch': tx['epoch']=0; cert=ia.sign(tx)
   elif kind=='excess_budget': tx['amount']=1001; cert=ia.sign(tx)
   att=attest(aa,tx)
   if kind=='stale_attestation': att=attest(aa,tx,issued=900)
   elif kind=='attestation_other_request': att=attest(aa,tx,request_hash='0'*64)
   elif kind=='unapproved_measurement': att=attest(aa,tx,measurement='modified-build')
   accepted,reason=mon.check(tx,cert,att); mon.close()
   rows.append(dict(scenario=kind,seed=seed,signature_only=1,shared_policy_bypassed=1,proposed=int(accepted),reason=reason))
 assert sum(r['proposed'] for r in rows)==0
 with (OUT/'attack_trials.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader();w.writerows(rows)
 return {k:sum(r['proposed'] for r in rows if r['scenario']==k) for k in kinds}
def benign():
 ia,aa=Issuer(),Issuer(); lat=[]; accepted=0
 for seed in range(30):
  rng=random.Random(seed); mon=Monitor(ia,aa,cap=100000)
  for i in range(100):
   tx=tx_for(seed*100+i,rng.randint(1,100)); cert=ia.sign(tx); att=attest(aa,tx)
   t=time.perf_counter_ns(); ok,_=mon.check(tx,cert,att); lat.append((time.perf_counter_ns()-t)/1e6);accepted+=ok
  mon.close()
 assert accepted==3000
 return dict(n=3000,accepted=accepted,p50_ms=float(statistics.median(lat)),p95_ms=sorted(lat)[int(.95*len(lat))-1],p99_ms=sorted(lat)[int(.99*len(lat))-1],mean_ms=statistics.mean(lat))
def residual():
 ia,aa=Issuer(),Issuer(); cap_rows=[]
 for cap in (100,250,500):
  mon=Monitor(ia,aa,cap=cap); value=0; charge=0; count=0
  # The issuer has been compromised; all malicious requests have valid evidence.
  for i in range(100):
   tx=tx_for(i,9,chain=('EVM','UTXO','ED25519')[i%3]);cert=ia.sign(tx)
   ok,_=mon.check(tx,cert,attest(aa,tx))
   if ok: value+=9; charge+=10; count+=1
  assert charge<=cap;mon.close()
  cap_rows.append(dict(cap=cap,attempted_value=900,accepted_value=value,reserved_including_fees=charge,accepted_count=count))
 return cap_rows
def race():
 ia,aa=Issuer(),Issuer(); trials=[]
 with tempfile.TemporaryDirectory() as d:
  for rep in range(20):
   p=str(Path(d)/f'{rep}.db');m=Monitor(ia,aa,cap=100,path=p);m.close()
   args=[]
   for i in range(64):
    tx=tx_for(i,19,chain=('EVM','UTXO')[i%2]);args.append((tx,ia.sign(tx),attest(aa,tx)))
   def worker(arg):
    mon=Monitor(ia,aa,cap=100,path=p)
    try: return mon.check(*arg)[0]
    finally: mon.close()
   with ThreadPoolExecutor(max_workers=16) as ex: admitted=sum(ex.map(worker,args))
   db=sqlite3.connect(p);spent=db.execute('SELECT spent FROM budget').fetchone()[0];db.close()
   assert admitted==5 and spent==100;trials.append(dict(rep=rep,admitted=admitted,reserved=spent))
 return trials
def ablations():
 ia,aa=Issuer(),Issuer(); out=[]
 for omit in ('binding','operation','replay','budget','epoch','expiry','attestation'):
  mon=Monitor(ia,aa,cap=100,omit=(omit,));tx=tx_for(1,9);cert=ia.sign(tx)
  if omit=='binding':tx['recipient']='attacker'
  elif omit=='operation':tx['operation']='delegate';cert=ia.sign(tx)
  elif omit=='replay':assert mon.check(tx,cert,attest(aa,tx))[0]
  elif omit=='budget':tx['amount']=1000;cert=ia.sign(tx)
  elif omit=='epoch':tx['epoch']=0;cert=ia.sign(tx)
  elif omit=='expiry':tx['expires']=999;cert=ia.sign(tx)
  att=attest(aa,tx,issued=900) if omit=='attestation' else attest(aa,tx)
  ok,why=mon.check(tx,cert,att);mon.close();assert ok
  out.append(dict(omitted=omit,bypass_accepted=int(ok),reason=why))
 return out
def outage():
 ia,aa=Issuer(),Issuer();out=[]
 for fraction in (0,.01,.05,.10):
  mon=Monitor(ia,aa);held=0
  for i in range(1000):
   tx=tx_for(i,1); cert=ia.sign(tx);att=attest(aa,tx,issued=900 if i<int(1000*fraction) else NOW)
   held+=not mon.check(tx,cert,att)[0]
  mon.close();assert held==int(1000*fraction);out.append(dict(stale_fraction=fraction,held=held,total=1000))
 return out
def state_explore():
 # Exhaustive reachable states of an abstract two-intent, one-epoch ledger.
 # Non-deterministic reserve/sign/fail/finalize/revoke actions, bounded depth.
 # Issued reservations are retained after sign/fail/finalize; never recycled.
 # State: (status of intent0,status of intent1,spent,epoch,paused)
 init=(0,0,0,1,0);front={init};seen={init};trans=0
 for depth in range(8):
  nxt=set()
  for state in front:
   a,b,spent,epoch,paused=state;statuses=[a,b];assert spent<=3
   for i,cost in enumerate((1,2)):
    st=statuses[i]
    if st==0 and not paused and spent+cost<=3:
     ns=statuses.copy();ns[i]=1;nxt.add((*ns,spent+cost,epoch,paused));trans+=1
    if st==1:
     for v in (2,3): # signature released or ambiguous failure
      ns=statuses.copy();ns[i]=v;nxt.add((*ns,spent,epoch,paused));trans+=1
    if st in (2,3):
     ns=statuses.copy();ns[i]=4;nxt.add((*ns,spent,epoch,paused));trans+=1
   if epoch==1:nxt.add((a,b,spent,2,1));trans+=1
  for state in nxt:
   a,b,spent,epoch,paused=state
   assert spent==sum(c for s,c in zip((a,b),(1,2)) if s!=0)
   assert epoch!=2 or paused==1
  front=nxt-seen;seen|=nxt
  if not front:break
 return dict(states=len(seen),transitions=trans,depth=depth+1,violations=0,scope='two intents, fixed costs 1 and 2, cap 3, one revocation, retained reservations')
def main():
 res=dict(attack_cases=attack_cases(),benign=benign(),residual=residual(),race=race(),ablations=ablations(),outage=outage(),model=state_explore(),environment=dict(python=platform.python_version(),platform=platform.platform(),processor=platform.processor(),cpu_count=os.cpu_count(),sqlite=sqlite3.sqlite_version))
 (OUT/'summary.json').write_text(json.dumps(res,indent=2))
 print(json.dumps(res,indent=2))
if __name__=='__main__':main()
