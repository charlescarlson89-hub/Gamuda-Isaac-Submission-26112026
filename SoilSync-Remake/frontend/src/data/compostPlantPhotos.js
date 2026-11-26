import basil from "../assets/suitable-plants/basil.jpg";
import chili from "../assets/suitable-plants/chili.jpg";
import garden from "../assets/suitable-plants/garden.jpg";
import hibiscus from "../assets/suitable-plants/hibiscus.jpg";
import papaya from "../assets/suitable-plants/papaya.jpg";
import turmeric from "../assets/suitable-plants/turmeric.jpg";
import { figma } from "./figma";

const commons = "https://commons.wikimedia.org/wiki/File:";
const licenses = {
  "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
  "CC BY-SA 3.0": "https://creativecommons.org/licenses/by-sa/3.0/",
  "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
  "CC0 1.0": "https://creativecommons.org/publicdomain/zero/1.0/",
};
const photos = [
  [/^potted herbs/i, basil, "Basil growing in a pot", "Basil_in_a_pot.jpg", "Zorro2212", "CC BY-SA 4.0"],
  [/^fruiting (crops|vegetables)/i, chili, "Capsicum growing in a home garden",
    "Capsicum_plant_(Capsicum_annuum)_in_Kerala.jpg", "Clintacc", "CC0 1.0"],
  [/fruit trees/i, papaya, "Papayas growing on a tree",
    "Papaya_tree_with_fruit.jpg", "Shiva Theerthagiri", "CC BY 4.0"],
  [/ornamentals|flowering balcony/i, hibiscus, "Hibiscus in bloom",
    "Hibiscus_Rosa-sinensis.jpg", "Aldrina A Manashe", "CC0 1.0"],
  [/spice tubers/i, turmeric, "Turmeric rhizomes",
    "Curcuma_longa_roots.jpg", "Simon A. Eugster", "CC BY-SA 3.0"],
  [/topsoil enrichment|soil factory beds/i, garden, "Planted raised garden bed",
    "Raised_bed.jpg", "Srl", "CC BY-SA 3.0"],
];
const originalPhotos = { Tomatoes: 0, "Leafy Greens": 1, Roses: 2, "Citrus Trees": 3, Monsteras: 4 };

export function compostPlantPhoto(name) {
  const photo = photos.find(([pattern]) => pattern.test(name));
  if (photo) {
    const [, src, alt, file, credit, license] = photo;
    return { src, alt, credit, license, source: commons + file, licenseUrl: licenses[license] };
  }
  const index = Object.hasOwn(originalPhotos, name) ? originalPhotos[name] : /^leafy (greens|vegetables)/i.test(name) ? 1 : null;
  if (index !== null) return { src: figma.fertilizer[index].src, alt: index === 1 ? "Leafy vegetables in a garden" : name };
  return null;
}
