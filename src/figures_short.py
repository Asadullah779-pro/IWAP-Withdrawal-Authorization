from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
R=Path(__file__).resolve().parents[1];F=R/'figures';S=json.loads((R/'results/summary.json').read_text());F.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(figsize=(7.16,3.2));ax.set(xlim=(0,7.16),ylim=(0,3.2));ax.axis('off')
ink='#233746'
def box(x,y,title,detail,color):
 w,h=2.03,.63
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.015,rounding_size=0.025',facecolor=color,edgecolor='#8b9ba8',linewidth=.7))
 ax.text(x+w/2,y+.43,title,ha='center',va='center',fontweight='bold',fontsize=8,color=ink)
 ax.text(x+w/2,y+.18,detail,ha='center',va='center',fontsize=7,color=ink)
def arrow(a,b,label='',offset=(0,0)):
 ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=9,color=ink,linewidth=.8))
 if label:ax.text((a[0]+b[0])/2+offset[0],(a[1]+b[1])/2+offset[1],label,ha='center',va='center',fontsize=6.5,bbox=dict(facecolor='white',edgecolor='none',pad=.5))
xs=[.08,2.54,5.0];green='#e2eee5';blue='#dceaf5'
box(xs[0],2.43,'Customer confirmation','Recipient, amount,\nasset, network',green)
box(xs[1],2.43,'Intent authority','Independent request\nand balance check',green)
box(xs[2],2.43,'State authority','One-use IDs; reserved capacity',green)
arrow((2.13,2.74),(2.52,2.74));arrow((4.59,2.74),(4.98,2.74))
box(xs[0],1.27,'Withdrawal backend','Potentially compromised\ntransaction constructor','#f4dfe0')
box(xs[1],1.27,'Independent signers','Verify exact bytes\nand all evidence',blue)
box(xs[2],1.27,'Blockchain network','Broadcast and reconcile\nsettlement',blue)
arrow((2.13,1.58),(2.52,1.58));arrow((4.59,1.58),(4.98,1.58))
arrow((3.56,2.41),(3.56,1.92),'intent',(-.23,0))
arrow((6.01,2.41),(4.60,1.92),'committed reservation',(.35,.12))
box(xs[1],.1,'Evidence verifier','Workload identity\nand evidence appraisal','#f7e8d5')
arrow((3.56,.75),(3.56,1.25),'fresh result',(.40,0))
ax.text(.08,.45,'Governance protects policy.\nBudgets have independent control.\nAlerts only restrict authority.',fontsize=7,color=ink)
fig.savefig(F/'architecture.pdf',bbox_inches='tight',pad_inches=.03);fig.savefig(F/'architecture.png',dpi=160,bbox_inches='tight',pad_inches=.03);plt.close(fig)
fig,ax=plt.subplots(figsize=(3.45,2.45));rs=S['residual'];x=list(range(len(rs)))
ax.bar([i-.18 for i in x],[r['accepted_value'] for r in rs],.35,color='#b9d8ce',label='Principal')
ax.bar([i+.18 for i in x],[r['reserved_including_fees'] for r in rs],.35,color='#b7cfe5',label='Principal + fee ceiling')
ax.set_xticks(x,[str(r['cap']) for r in rs]);ax.set_xlabel('Fixed epoch budget (synthetic units)',fontsize=7.5);ax.set_ylabel('Admitted / reserved units',fontsize=7.5);ax.set_ylim(0,650);ax.legend(frameon=False,fontsize=7,loc='upper left');ax.tick_params(labelsize=7);fig.tight_layout(pad=.5)
fig.savefig(F/'loss_bound.pdf',bbox_inches='tight');fig.savefig(F/'loss_bound.png',dpi=180,bbox_inches='tight');plt.close(fig)
b=S['benign'];(R/'results/macros.tex').write_text('\\newcommand{\\LocalMedian}{%.3f}\n\\newcommand{\\LocalPninetyfive}{%.3f}\n\\newcommand{\\LocalPninetynine}{%.3f}\n'%(b['p50_ms'],b['p95_ms'],b['p99_ms']))
