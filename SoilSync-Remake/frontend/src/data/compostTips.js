const epa = { label: "EPA home composting guide", url: "https://www.epa.gov/recycle/composting-home" };
const cornell = { label: "Cornell composting guide", url: "https://compost.css.cornell.edu/faq.html" };

// Short editorial tips, checked against the linked guides. No provider call is needed.
export const compostTips = [
  { id: "small", text: "Chop bulky scraps before composting. Smaller pieces break down more easily.", source: epa },
  { id: "browns", text: "Keep dry leaves or plain shredded cardboard handy to balance food scraps.", source: epa },
  { id: "moisture", text: "Aim for a damp, squeezed-sponge feel in an aerobic pile—not a soggy mix.", source: epa },
  { id: "smell", text: "A smelly aerobic pile may need dry browns and mixing for airflow.", source: epa },
  { id: "stickers", text: "Peel off produce stickers and remove packaging before adding fruit scraps.", source: epa },
  { id: "cardboard", text: "Use shredded cardboard without wax, tape or glue in a home compost pile.", source: epa },
  { id: "cover", text: "Cover food scraps with browns to help discourage pests.", source: epa },
  { id: "avoid", text: "Keep meat, dairy and greasy leftovers out of a beginner backyard pile.", source: epa },
  { id: "dry", text: "A dry aerobic pile slows down. Add moisture gradually and mix.", source: epa },
  { id: "coffee", text: "Coffee grounds count as greens; pair them with dry browns.", source: epa },
  { id: "bin", text: "Choose a composting spot with drainage and easy access for regular care.", source: epa },
  { id: "cold", text: "Cold composting takes longer with less turning. Cover food scraps with browns and keep airflow.", source: epa },
  { id: "patience", text: "Composting time varies with materials and care. A calendar cannot certify readiness.", source: cornell },
  { id: "cure", text: "Let compost cure after active breakdown; looking finished does not mean fully stable.", source: cornell },
  { id: "roots", text: "Unfinished compost can harm plants. Check maturity before applying it.", source: cornell },
  { id: "soil", text: "Plant nutrient needs vary. A soil test is more useful than guessing from a photo.", source: cornell },
];

export function dailyCompostTip(day, offset = 0) {
  const days = Math.floor(Date.parse(`${day}T00:00:00Z`) / 86400000);
  const start = Number.isFinite(days) ? days : 0;
  const step = Number.isFinite(offset) ? Math.trunc(offset) : 0;
  const index = ((start + step) % compostTips.length + compostTips.length) % compostTips.length;
  return compostTips[index];
}
