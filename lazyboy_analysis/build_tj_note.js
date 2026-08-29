const fs=require('fs');
const {Document,Packer,Paragraph,TextRun,HeadingLevel,AlignmentType,Table,TableRow,TableCell,
       WidthType,ShadingType,BorderStyle,convertInchesToTwip}=require('docx');

const INK="1F1D1A", MUTED="5C574F", RULE="D9D3C8", BAND="F0EBE0", ACCENT="7A2E1E";
const W=9360; // content width in DXA (Letter, 1" margins)

const p=(text,o={})=>new Paragraph({
  spacing:{before:o.before??0,after:o.after??120},
  alignment:o.align,
  border:o.rule?{bottom:{style:BorderStyle.SINGLE,size:6,color:RULE,space:6}}:undefined,
  children:[new TextRun({text,size:o.size??21,bold:o.bold,italics:o.italics,
                         color:o.color??INK,font:o.font??"Calibri"})]});

const rich=(runs,o={})=>new Paragraph({spacing:{before:o.before??0,after:o.after??120},
  children:runs.map(r=>new TextRun({text:r.t,bold:r.b,italics:r.i,size:o.size??21,
                                    color:r.c??INK,font:"Calibri"}))});

const h1=t=>new Paragraph({heading:HeadingLevel.HEADING_1,spacing:{before:320,after:140},
  children:[new TextRun({text:t,size:26,bold:true,color:INK,font:"Calibri"})]});

function table(cols,rows,opts={}){
  const widths=opts.widths||cols.map(()=>Math.floor(W/cols.length));
  const cell=(txt,{bold,align,shade,color}={})=>new TableCell({
    width:{size:0,type:WidthType.DXA},
    shading:shade?{type:ShadingType.CLEAR,fill:shade,color:"auto"}:undefined,
    margins:{top:70,bottom:70,left:110,right:110},
    borders:{top:{style:BorderStyle.SINGLE,size:2,color:RULE},
             bottom:{style:BorderStyle.SINGLE,size:2,color:RULE},
             left:{style:BorderStyle.NONE},right:{style:BorderStyle.NONE}},
    children:[new Paragraph({alignment:align,spacing:{after:0},
      children:[new TextRun({text:txt,size:19,bold,color:color??INK,font:"Calibri"})]})]});
  const header=new TableRow({tableHeader:true,children:cols.map((c,i)=>
    cell(c,{bold:true,shade:BAND,align:i?AlignmentType.RIGHT:AlignmentType.LEFT}))});
  const body=rows.map(r=>new TableRow({children:r.map((v,i)=>
    cell(String(v),{align:i?AlignmentType.RIGHT:AlignmentType.LEFT,
                    bold:typeof v==='string'&&v.startsWith('*'),
                    color:(typeof v==='string'&&v.startsWith('*'))?ACCENT:undefined}))}));
  // strip the '*' emphasis marker after using it
  body.forEach(row=>row.root.filter(c=>c.root).forEach(()=>{}));
  return new Table({columnWidths:widths,width:{size:W,type:WidthType.DXA},rows:[header,...body]});
}
const clean=v=>typeof v==='string'&&v.startsWith('*')?v.slice(1):v;
const T=(cols,rows,opts)=>table(cols,rows.map(r=>r.map(clean)),opts);

const doc=new Document({
  styles:{default:{document:{run:{font:"Calibri",size:21,color:INK}}}},
  sections:[{
    properties:{page:{size:{width:12240,height:15840},
                margin:{top:1300,bottom:1300,left:1440,right:1440}}},
    children:[

new Paragraph({spacing:{after:60},children:[new TextRun({text:"UpliftIQ  ·  competitive pricing note",
  size:17,color:MUTED,font:"Calibri",allCaps:true})]}),
new Paragraph({spacing:{after:80},children:[new TextRun({
  text:"Two things visible from outside La-Z-Boy",size:34,bold:true,color:INK,font:"Calibri"})]}),
p("Prepared for TJ Linz  ·  29 August 2026",{color:MUTED,size:19,after:80,rule:true}),

p("Everything below comes from public web data collected this week — La-Z-Boy's own store pages and Slumberland's catalogue. No La-Z-Boy data was used, which is the point: both findings are checkable against your internal numbers in an afternoon, and if they hold they are visible to your competitors too.",
  {after:200,color:MUTED}),

h1("1.  The same recliner sells for $769 to $1,699 across your own stores"),

p("La-Z-Boy.com prices are set per store. Setting a store preference and holding the product and the fabric constant, we priced one Pinnacle rocking recliner in cover B153808 across every store in your locator — 332 in the United States.",{after:140}),

T(["Same chair, same cover, 332 US stores",""],[
  ["Distinct selling prices","26"],
  ["Range","$769 – $1,699  (2.2×)"],
  ["Most common price","$1,189, at 204 stores"],
  ["Stores running a promotion","283"],
  ["Stores running none","49"],
  ["Distinct “was” prices","18  ($1,239 – $2,319)"],
],{widths:[6100,3260]}),

p("",{after:100}),
p("Both halves of the price move, not just the discount. The reference price itself is set locally — an identical chair is anchored at $1,239 in one market and $2,319 in another — so this is not one national list price with local promotions applied to it.",{after:140}),

rich([{t:"Indiana contains both extremes. "},{t:"Indianapolis sells it at $1,699 with no promotion; Fort Wayne sells it at $789, 47% off. ",b:true},
      {t:"California (19 stores) and Oregon (8 stores) run no promotion at all, while Texas (26 stores) runs 43% off."}],{after:140}),

T(["Selected stores","Price","Discount"],[
  ["Indianapolis, IN","$1,699","none"],
  ["California — 19 stores","$1,549","none"],
  ["Arizona — 11 stores","$1,399","25%"],
  ["*204 stores (the norm)","*$1,189","*30%"],
  ["Texas — 26 stores","$1,059","43%"],
  ["Albuquerque, NM","$979","30%"],
  ["Fort Wayne, IN","$789","47%"],
  ["Springfield, MO","$769","40%"],
],{widths:[4600,2380,2380]}),

p("",{after:100}),
p("A store's position is stable across products. Across the same 332 stores, 26 Pinnacle prices and 23 prices for a second recliner produce only 28 combinations — a store sits in one pricing zone for its whole catalogue rather than being priced product by product.",{after:60}),

new Paragraph({pageBreakBefore:true,children:[]}),

h1("2.  Slumberland beats your own Minneapolis stores where the margin is"),

p("Slumberland is Minnesota-based, so the fair comparison is your four Minnesota stores — Edina, Maple Grove, St. Cloud and Woodbury, which price identically and sit in the zone shared by 204 of 332 US stores. We compared the 35 models both carry, at the cheapest way a shopper can buy each one.",{after:140}),

T(["Across 35 models both carry","Median gap"],[
  ["All models","Slumberland 7% cheaper"],
  ["*Recliners  (22 models)","*Slumberland 15% cheaper"],
  ["Motion sofas  (13 models)","level"],
],{widths:[5600,3760]}),

p("",{after:120}),
p("The aggregate hides an inversion. Slumberland undercuts you on the mid and premium recliners, while your own stores undercut Slumberland sharply at the opening price point.",{after:140}),

T(["Where Slumberland is cheaper","Slumberland","Your MN stores","Gap"],[
  ["Pinnacle Platinum Power Lift Recliner","$1,280","$1,959","−35%"],
  ["Brooks Reclining Loveseat","$980","$1,319","−26%"],
  ["Brooks Reclining Sofa","$1,000","$1,329","−25%"],
  ["Liam Bronze Power Lift Recliner","$1,100","$1,399","−21%"],
  ["Jean Bronze Power Lift Recliner","$850","$1,049","−19%"],
],{widths:[4000,1700,1960,1700]}),

p("",{after:140}),

T(["Where your stores are cheaper","Slumberland","Your MN stores","Gap"],[
  ["*Liam Rocking Recliner","*$630","*$399","*+58%"],
  ["*Norton Rocking Recliner","*$600","*$399","*+50%"],
  ["*Collage Rocking Recliner","*$400","*$299","*+34%"],
  ["Ava Rocking Recliner","$900","$799","+13%"],
  ["James Reclining Loveseat","$1,700","$1,479","+15%"],
],{widths:[4000,1700,1960,1700]}),

p("",{after:120}),
p("Liam, Norton, Collage and Vail all anchor at exactly $799 in Minneapolis and sell at $299 to $559 — one doorbuster ladder off a common anchor. Slumberland cannot match $299.",{after:140}),

rich([{t:"The net effect: a shopper in your Minneapolis store gets the cheapest entry point and the most expensive step-up. ",b:true},
      {t:"You win the traffic and Slumberland wins the conversion — on your own product, in your own home market, in the zone that covers roughly 60% of your US stores."}],{after:200}),

h1("Method and limits"),

p("Collected 29 August 2026 from public pages. Store prices were read by setting La-Z-Boy.com's own store preference; Slumberland's from its public catalogue feed. Prices are what a shopper is quoted, so both sides include whatever promotion was running.",{after:120}),

p("Model matching is on model name, form and drive type, comparing the cheapest available cover against the cheapest stocked SKU — how a shopper would actually buy each model, not an identical-cover match. 36 Canadian stores are excluded: the pages state no currency, and pooling them would confuse an exchange rate with a pricing decision.",{after:120}),

p("This is one week and one snapshot. A weekly collection is now running, which will show whether the Minneapolis entry-price promotion is structural or a single event — the answer changes what the second finding means.",{after:120}),

p("Philip Carls  ·  UpliftIQ  ·  philip@upliftiq.io",{color:MUTED,size:19,before:200}),

]}]});

Packer.toBuffer(doc).then(b=>{fs.writeFileSync(
  '/home/user/vols/lazyboy_analysis/deliverables/La-Z-Boy_pricing_note_2026-08-29.docx',b);
  console.log('written');});
