import hot1 from "../assets/compost-guides/hot-1.svg";
import hot2 from "../assets/compost-guides/hot-2.svg";
import hot3 from "../assets/compost-guides/hot-3.svg";
import cold1 from "../assets/compost-guides/cold-1.svg";
import cold2 from "../assets/compost-guides/cold-2.svg";
import cold3 from "../assets/compost-guides/cold-3.svg";
import bokashi1 from "../assets/compost-guides/bokashi-1.svg";
import bokashi2 from "../assets/compost-guides/bokashi-2.svg";
import bokashi3 from "../assets/compost-guides/bokashi-3.svg";
import atlasStages from "../assets/compost-guides/blender-rice-water-stages.png";

export const compostGuideImages = {
  "hot-1": { src: hot1, alt: "Separate plant scraps and dry browns, then chop larger scraps." },
  "hot-2": { src: hot2, alt: "Mix greens and browns in a ventilated pile with air and moisture." },
  "hot-3": { src: hot3, alt: "Turn the pile, measure its temperature, then allow cooling and curing." },
  "cold-1": { src: cold1, alt: "Collect food scraps and dry leaves or cardboard separately." },
  "cold-2": { src: cold2, alt: "Add material gradually and cover food with browns in an airy bin." },
  "cold-3": { src: cold3, alt: "Wait months for decomposition and harvest only fully finished material." },
  "bokashi-1": { src: bokashi1, alt: "Prepare a Bokashi bucket with a tap and a supply of inoculated bran." },
  "bokashi-2": { src: bokashi2, alt: "Layer food and bran, press out air, reseal the lid and drain the tap." },
  "bokashi-3": { src: bokashi3, alt: "Ferment the full sealed bucket for about two weeks, then finish breaking down the contents away from plant roots." },
  "blender-1": { src: atlasStages, position: "left top", alt: "Blender with raw fruit and vegetable scraps." },
  "blender-2": { src: atlasStages, position: "center top", alt: "A soil bed cutaway showing the blended scraps being mixed into the lower layer." },
  "blender-3": { src: atlasStages, position: "right top", alt: "A dry topsoil layer covering the buried mixture." },
  "rice-water-1": { src: atlasStages, position: "left bottom", alt: "Cloudy rice rinse water in a jar covered with breathable cloth." },
  "rice-water-2": { src: atlasStages, position: "center bottom", alt: "A strainer separating the pale liquid starter from the curds." },
  "rice-water-3": { src: atlasStages, position: "right bottom", alt: "A compost bucket, spray bottle, shredded cardboard, and soil for the finishing stage." },
};

export const compostMethodDetails = {
  hot: {
    use: "Kangkung or sawi stems, banana peels, papaya peels and coffee grounds. Add dry leaves or plain shredded cardboard for browns.",
    avoid: "Meat, bones, dairy, oily curries, pet waste and diseased plants.",
    gardenExamples: "Cili padi, terung (eggplant) and bendi (okra).",
    stageTips: {
      "hot-2": "Aim for a pile about 90 cm wide, deep and tall so it can hold heat. The mix should feel like a wrung-out sponge.",
      "hot-3": "Once turning no longer reheats the pile and food scraps are no longer visible, allow at least four weeks for curing before garden use.",
    },
  },
  cold: {
    use: "Long bean ends, cabbage trimmings, potato peels and crushed eggshells. Keep dry leaves or plain shredded cardboard nearby to cover each addition.",
    avoid: "Meat, fish, dairy and oily leftovers.",
    gardenExamples: "Sawi, bayam, kailan, pandan, serai (lemongrass) and daun kari (curry leaf).",
    stageTips: {
      "cold-2": "Place an open-bottom bin on soil if its design allows. In dry weather, add a little water if the mix dries out.",
      "cold-3": "If your bin has a bottom hatch, collect the mature compost there while newer scraps break down above it.",
    },
  },
  bokashi: {
    use: "Use plant scraps, small plain meat or fish trimmings, and small bones if your sealed Bokashi kit accepts them.",
    avoid: "Keep out large bones, spoiled scraps, oil and excess liquid such as soup.",
    gardenExamples: "Bunga raya (hibiscus), bougainvillea, halia (ginger) and kunyit (turmeric). Use only after the fermented scraps have fully broken down in soil or compost.",
    stageTips: {
      "bokashi-1": "The sealed bucket can be kept indoors in a shaded spot. Plan where the fermented scraps will finish breaking down before you start.",
      "bokashi-2": "Drain the tap every few days while keeping the lid sealed. Follow the kit’s instructions for handling the liquid.",
    },
  },
  blender: {
    stageTips: {
      "blender-3": "Treat the time range as a check-in estimate. Keep the mixture away from roots until scraps have fully broken down.",
    },
  },
  "rice-water": {
    stageTips: {
      "rice-water-2": "Label the starter for composting only and keep it separate from food and drinks.",
      "rice-water-3": "Let the buried scraps continue breaking down if they are still visible. Keep unfinished material away from plant roots.",
    },
  },
};

export const approvedRecipes = (recipes) => recipes.filter((recipe) =>
  recipe.method && recipe.active !== false,
);
