import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowDown,
  ArrowUpRight,
  Check,
  ChevronDown,
  Leaf,
  Menu,
  Pause,
  Play,
  ScanLine,
  Sprout,
  X,
} from "lucide-react";
import { Brand } from "../components/Brand";
import scraps from "../assets/food-scraps.jpg";
import gardenVideo from "../assets/landing-scraps-compost.mp4";
import gardenPoster from "../assets/landing-scraps-compost-poster.jpg";
import "./LandingPage.css";
import LeaffyMascot from "../components/LeaffyMascot";

const chapters = [
  {
    label: "The everyday beginning",
    title: "A peel. A core. A possibility.",
    text: "Your kitchen scraps can have another chapter. Start by separating suitable food waste.",
    icon: Leaf,
    caption: "01 / HOUSEHOLD FOOD SCRAPS",
    detail: "Small scraps. A fresh start.",
  },
  {
    label: "A little clarity",
    title: "Snap it. Understand it.",
    text: "Use an AI-assisted scan, then review the result. Learn what belongs in your compost.",
    icon: ScanLine,
    caption: "02 / AI-ASSISTED IDENTIFICATION",
    detail: "A photo starts the conversation.",
  },
  {
    label: "The hands-on part",
    title: "Prepare. Compost. Give it time.",
    text: "Prepare suitable scraps, mix greens with browns, and follow your household composting guide.",
    icon: Sprout,
    caption: "03 / PREPARATION & COMPOSTING",
    detail: "Good things take a little care.",
  },
  {
    label: "Back to the beginning",
    title: "Feed the soil. Grow something.",
    text: "Use mature compost with care. Build a routine that brings useful materials back to your garden.",
    icon: Leaf,
    caption: "04 / A MORE CIRCULAR EVERYDAY",
    detail: "From your kitchen, back to the earth.",
  },
];

const questions = [
  [
    "What is SoilSync?",
    "SoilSync is TEDA BYTE’s Food Waste & Home Gardening Companion. It helps households identify scraps, learn home composting and build a greener daily routine.",
  ],
  [
    "Can I use AI on the website?",
    "SoilSync uses Gemini to identify photographed materials against our waste catalogue. If AI is unavailable, the scan shows a clear status instead of guessing. Leaffy can also help with project questions.",
  ],
  [
    "How do EcoPoints work?",
    "Daily check-in earns 10 EcoPoints, a new scan with compostable waste earns 50, and each completed weekly batch quest earns 100. Chat earns zero. Repeated uploads and claims do not earn or spend points twice.",
  ],
  [
    "Are the rewards real vouchers?",
    "Partner perks remain project concepts; no real voucher or product is issued. Your claims and point balance are saved to your account. Each catalogue reward can be claimed once.",
  ],
  [
    "Does completing the checklist mean my compost is ready?",
    "The checklist records your progress. Compost readiness depends on your materials and conditions; ticking a box does not prove maturity or nutrient content.",
  ],
  [
    "Where is my information saved?",
    "Your profile and activity are saved to your SoilSync account. Weekly check-in photos are private. Scan photos are sent to Google Gemini for identification. Leaffy conversations remain in this page and clear when you leave.",
  ],
];

function StoryScene({ stage }) {
  return (
    <div className={`lp-scene lp-scene-${stage}`}>
      <div className="lp-orbit" aria-hidden="true" />
      {stage < 2 ? (
        <div className={stage === 1 ? "lp-scan-frame" : "lp-scrap-frame"}>
          <img
            src={scraps}
            alt="A banana peel, an example of household food scraps"
            loading="lazy"
            width="1517"
            height="1424"
          />
          {stage === 1 && (
            <>
              <div className="lp-scan-line" aria-hidden="true" />
              <span className="lp-example">
                <ScanLine size={16} aria-hidden="true" /> Illustration · banana
                peel
              </span>
            </>
          )}
        </div>
      ) : (
        <svg
          className="lp-grow-art"
          viewBox="0 0 400 340"
          role="img"
          aria-label={
            stage === 2
              ? "Food scraps and dry leaves layered in a home compost container"
              : "A leafy plant growing in mature compost"
          }
        >
          <ellipse cx="200" cy="300" rx="146" ry="18" fill="#233b2720" />
          <path d="M85 176H315L286 287Q200 313 114 287Z" fill="#806043" />
          <path d="M96 219H304L294 250H106Z" fill="#b59364" />
          <path d="M106 250H294L286 287Q200 313 114 287Z" fill="#53402c" />
          <ellipse cx="200" cy="176" rx="115" ry="29" fill="#3d3224" />
          {stage === 2 ? (
            <g>
              <path
                d="M125 160Q151 197 184 159Q174 204 145 196Q119 185 125 160"
                fill="#e6be63"
              />
              <path
                d="M219 172Q203 127 243 121Q272 154 219 172"
                fill="#8c9a58"
              />
              <path
                d="M256 180Q287 152 288 187Q272 202 256 180"
                fill="#b6a26a"
              />
              <path
                d="M110 124L128 113M160 104L180 119M271 102L286 90"
                stroke="#a77a43"
                strokeWidth="7"
                strokeLinecap="round"
              />
              <path
                d="M191 147Q182 129 190 114M208 115Q201 93 209 76"
                stroke="#98a182"
                strokeWidth="3"
                fill="none"
                strokeLinecap="round"
              />
            </g>
          ) : (
            <g>
              <path
                d="M201 177Q210 105 201 43"
                fill="none"
                stroke="#45633a"
                strokeWidth="7"
                strokeLinecap="round"
              />
              <path d="M205 125Q130 131 118 67Q182 59 205 125" fill="#70884a" />
              <path d="M204 91Q265 99 285 35Q220 30 204 91" fill="#456b38" />
              <path d="M202 53Q156 43 166 0Q212 5 202 53" fill="#9aab68" />
              <path
                d="M137 79L193 115M273 46L214 83"
                stroke="#c4d19c"
                strokeWidth="2"
              />
              <path
                d="M200 177L183 210M201 187L222 220"
                stroke="#b9a980"
                strokeWidth="3"
              />
            </g>
          )}
        </svg>
      )}
    </div>
  );
}

export default function LandingPage() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [activeChapter, setActiveChapter] = useState(0);
  const [motionAllowed, setMotionAllowed] = useState(false);
  const [userPaused, setUserPaused] = useState(false);
  const [videoFailed, setVideoFailed] = useState(false);
  const [playing, setPlaying] = useState(false);
  const rootRef = useRef(null);
  const heroRef = useRef(null);
  const videoRef = useRef(null);
  const appPath = "/login";

  useEffect(() => {
    const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () =>
      setMotionAllowed(!preference.matches && !navigator.connection?.saveData);
    update();
    preference.addEventListener("change", update);
    return () => preference.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !motionAllowed || videoFailed) return;
    let inView = true;
    const sync = () => {
      if (userPaused || document.hidden || !inView) video.pause();
      else video.play().catch(() => setPlaying(false));
    };
    const observer =
      "IntersectionObserver" in window
        ? new IntersectionObserver(([entry]) => {
            inView = entry.isIntersecting;
            sync();
          })
        : null;
    observer?.observe(heroRef.current);
    document.addEventListener("visibilitychange", sync);
    sync();
    return () => {
      observer?.disconnect();
      document.removeEventListener("visibilitychange", sync);
      video.pause();
    };
  }, [motionAllowed, userPaused, videoFailed]);

  useEffect(() => {
    if (!("IntersectionObserver" in window)) return;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("lp-entered");
          }
        });
      },
      { rootMargin: "-12% 0px -18% 0px", threshold: 0.25 },
    );
    rootRef.current
      .querySelectorAll("[data-reveal]")
      .forEach((element) => observer.observe(element));
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const elements = Array.from(
      rootRef.current.querySelectorAll("[data-chapter]"),
    );
    let frame;
    const update = () => {
      const center = window.innerHeight / 2;
      const visible = elements
        .map((element) => ({ element, rect: element.getBoundingClientRect() }))
        .filter(({ rect }) => rect.bottom > 0 && rect.top < window.innerHeight);
      if (!visible.length) return;
      const nearest = visible.reduce((a, b) =>
        Math.abs(a.rect.top + a.rect.height / 2 - center) <
        Math.abs(b.rect.top + b.rect.height / 2 - center)
          ? a
          : b,
      );
      setActiveChapter(Number(nearest.element.dataset.chapter));
    };
    const onScroll = () => {
      window.cancelAnimationFrame(frame);
      frame = window.requestAnimationFrame(update);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    update();
    return () => {
      window.cancelAnimationFrame(frame);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, []);

  useEffect(() => {
    if (!menuOpen) return;
    const close = (event) => {
      if (event.key === "Escape") {
        setMenuOpen(false);
        document.getElementById("lp-menu-toggle")?.focus();
      }
    };
    document.addEventListener("keydown", close);
    return () => document.removeEventListener("keydown", close);
  }, [menuOpen]);

  const jumpToSection = (event) => {
    event.preventDefault();
    setMenuOpen(false);
    const target = document.getElementById(
      event.currentTarget.getAttribute("href").slice(1),
    );
    target?.scrollIntoView({ behavior: motionAllowed ? "smooth" : "instant" });
    target?.focus({ preventScroll: true });
  };

  return (
    <div className="lp" ref={rootRef}>
      <a className="lp-skip" href="#lp-main" onClick={jumpToSection}>
        Skip to content
      </a>
      <header className="lp-header">
        <Link
          to="/"
          className="lp-logo"
          aria-label="SoilSync by TEDA BYTE home"
        >
          <Brand />
          <span>BY TEDA BYTE</span>
        </Link>
        <button
          type="button"
          id="lp-menu-toggle"
          className="lp-menu"
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          aria-expanded={menuOpen}
          aria-controls="lp-navigation"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          {menuOpen ? <X aria-hidden="true" /> : <Menu aria-hidden="true" />}
        </button>
        <nav
          id="lp-navigation"
          aria-label="Landing page"
          className={`lp-links ${menuOpen ? "is-open" : ""}`}
        >
          <a href="#how-it-works" onClick={jumpToSection}>
            The SoilSync loop
          </a>
          <a href="#our-purpose" onClick={jumpToSection}>
            Our purpose
          </a>
          <a href="#questions" onClick={jumpToSection}>
            FAQs
          </a>
          <Link className="lp-nav-cta" to={appPath}>
            Explore SoilSync <ArrowUpRight size={18} aria-hidden="true" />
          </Link>
        </nav>
      </header>

      <main id="lp-main" tabIndex={-1}>
        <section
          className="lp-hero"
          ref={heroRef}
          aria-labelledby="lp-hero-title"
        >
          <div className="lp-hero-media" aria-hidden="true">
            <img
              src={gardenPoster}
              className="lp-poster"
              alt=""
              width="1280"
              height="720"
              fetchPriority="high"
            />
            {motionAllowed && !videoFailed && (
              <video
                ref={videoRef}
                src={gardenVideo}
                poster={gardenPoster}
                autoPlay
                muted
                loop
                playsInline
                preload="metadata"
                tabIndex={-1}
                onPlay={() => setPlaying(true)}
                onPause={() => setPlaying(false)}
                onError={() => {
                  setVideoFailed(true);
                  setPlaying(false);
                }}
              />
            )}
          </div>
          <div className="lp-hero-copy">
            <span className="lp-kicker">
              <span /> SMALL SCRAPS. BIG CHANGE.
            </span>
            <h1 id="lp-hero-title">
              Your Food Scraps <br />
              Deserve a <br />
              <em>Second Life.</em>
            </h1>
            <p>
              From kitchen leftovers to a greener tomorrow. Find your next small
              step with SoilSync.
            </p>
            <div className="lp-actions">
              <Link className="lp-btn lp-btn-outline" to={appPath}>
                Explore SoilSync <ArrowUpRight size={20} aria-hidden="true" />
              </Link>
            </div>
            <p className="lp-prototype-note">
              Frontend preview · sample scans and household guides.
            </p>
          </div>
          <div className="lp-hero-bottom">
            <a href="#how-it-works" onClick={jumpToSection}>
              FOLLOW THE LOOP <ArrowDown size={17} aria-hidden="true" />
            </a>
            <span className="lp-film-caption">
              A LITTLE CARE. NEW POSSIBILITIES.
            </span>
            {motionAllowed && !videoFailed && (
              <button
                type="button"
                className="lp-video-control"
                onClick={() => {
                  setUserPaused(playing);
                  if (!playing)
                    videoRef.current?.play().catch(() => setPlaying(false));
                }}
                aria-label={
                  playing ? "Pause background video" : "Play background video"
                }
              >
                {playing ? (
                  <Pause size={16} aria-hidden="true" />
                ) : (
                  <Play size={16} aria-hidden="true" />
                )}
                <span>{playing ? "Pause" : "Play"}</span>
              </button>
            )}
          </div>
        </section>

        <div className="lp-values">
          <span>
            <Leaf size={18} aria-hidden="true" /> Made for households
          </span>
          <span>
            <ScanLine size={18} aria-hidden="true" /> Guided by understanding
          </span>
          <span>
            <Sprout size={18} aria-hidden="true" /> Rooted in everyday care
          </span>
        </div>

        <section
          className="lp-section lp-story"
          id="how-it-works"
          tabIndex={-1}
          aria-labelledby="lp-story-title"
        >
          <div className="lp-section-heading" data-reveal>
            <div>
              <span className="lp-kicker">THE SOILSYNC LOOP</span>
              <h2 id="lp-story-title">Every ending can be a beginning.</h2>
            </div>
            <p>
              Four small steps.
              <br />A different way to see your scraps.
            </p>
          </div>
          <div className="lp-story-grid">
            <div
              className="lp-story-visual"
              id="lp-story-scene"
              role="group"
              aria-label={`Journey illustration: ${chapters[activeChapter].title}`}
            >
              <span className="lp-scene-caption">
                {chapters[activeChapter].caption}
              </span>
              <StoryScene stage={activeChapter} />
              <p className="lp-scene-detail">
                {chapters[activeChapter].detail}
              </p>
              <div
                className="lp-chapter-controls"
                aria-label="Choose a story illustration"
              >
                {chapters.map((chapter, index) => (
                  <button
                    type="button"
                    key={chapter.title}
                    aria-label={`0${index + 1}: ${chapter.title}`}
                    aria-pressed={activeChapter === index}
                    aria-controls="lp-story-scene"
                    onClick={() => {
                      setActiveChapter(index);
                      document
                        .getElementById(`lp-chapter-${index}`)
                        ?.scrollIntoView({
                          behavior: motionAllowed ? "smooth" : "instant",
                          block: "center",
                        });
                    }}
                  >
                    0{index + 1}
                  </button>
                ))}
              </div>
            </div>
            <div className="lp-chapters">
              {chapters.map((chapter, index) => (
                <article
                  key={chapter.title}
                  id={`lp-chapter-${index}`}
                  data-chapter={index}
                  data-reveal
                  className={`lp-chapter ${activeChapter === index ? "is-active" : ""}`}
                >
                  <span className="lp-chapter-number">
                    0{index + 1}
                    <chapter.icon size={24} aria-hidden="true" />
                  </span>
                  <span className="lp-kicker">{chapter.label}</span>
                  <h3>{chapter.title}</h3>
                  <p>{chapter.text}</p>
                  {index === 1 && (
                    <span className="lp-small-note">
                      Review AI suggestions before acting.
                    </span>
                  )}
                  {index === 3 && (
                    <Link to="/fertilizer" className="lp-text-link">
                      Find your composting guide{" "}
                      <ArrowUpRight size={18} aria-hidden="true" />
                    </Link>
                  )}
                </article>
              ))}
            </div>
          </div>
        </section>

        <section
          className="lp-purpose lp-section"
          id="our-purpose"
          tabIndex={-1}
          aria-labelledby="lp-purpose-title"
          data-reveal
        >
          <div className="lp-purpose-mark" aria-hidden="true">
            <Sprout size={60} strokeWidth={1.2} />
            <span>
              LESS WASTE.
              <br />
              <em>More possibility.</em>
            </span>
          </div>
          <div>
            <span className="lp-kicker">
              FOR YOUR HOME. FOR YOUR COMMUNITY.
            </span>
            <h2 id="lp-purpose-title">Change grows from the everyday.</h2>
            <p>
              You don’t need a perfect garden to begin. Just a little curiosity,
              a few suitable scraps, and a habit worth growing.
            </p>
            <ul>
              <li>
                <Check size={18} aria-hidden="true" /> Understand what you can
                compost.
              </li>
              <li>
                <Check size={18} aria-hidden="true" /> Care for your compost
                over time.
              </li>
              <li>
                <Check size={18} aria-hidden="true" /> Give mature compost a
                useful second life.
              </li>
            </ul>
            <Link className="lp-text-link" to={appPath}>
              Explore SoilSync <ArrowUpRight size={18} aria-hidden="true" />
            </Link>
          </div>
        </section>

        <section
          className="lp-section lp-faq"
          id="questions"
          tabIndex={-1}
          aria-labelledby="lp-faq-title"
        >
          <div>
            <span className="lp-kicker">BEFORE YOU BEGIN</span>
            <h2 id="lp-faq-title">A little more clarity.</h2>
            <p>
              Good questions.
              <br />
              Honest answers.
            </p>
          </div>
          <div>
            {questions.map(([title, text]) => (
              <details key={title}>
                <summary>
                  {title}
                  <ChevronDown size={19} aria-hidden="true" />
                </summary>
                <p>{text}</p>
              </details>
            ))}
          </div>
        </section>

        <section className="lp-cta" aria-labelledby="lp-cta-title" data-reveal>
          <Leaf size={30} aria-hidden="true" />
          <span className="lp-kicker">LET’S CLOSE THE LOOP</span>
          <h2 id="lp-cta-title">The next chapter starts in your kitchen.</h2>
          <p>One small scrap. One thoughtful choice.</p>
          <span className="lp-small-note">
            Household composting & gardening · prototype rewards only
          </span>
        </section>
      </main>

      <footer className="lp-footer">
        <div>
          <Link to="/" aria-label="SoilSync home">
            <Brand />
          </Link>
          <p>Food Waste & Home Gardening Companion</p>
        </div>
        <div>
          <strong>TEDA BYTE</strong>
          <p>Small scraps. Big change. · Capstone 2026</p>
        </div>
        <a
          href="https://www.pexels.com/video/sorting-out-compost-for-gardening-5910449/"
          target="_blank"
          rel="noreferrer"
        >
          Film: Anna Shvets / Pexels{" "}
          <ArrowUpRight size={15} aria-hidden="true" />
        </a>
      </footer>
      <LeaffyMascot />
    </div>
  );
}
