import React, { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowUpRight,
  Leaf,
  Moon,
  Send,
  Square,
  Sun,
  Trash2,
  X,
} from "lucide-react";
import {
  findLeaffyAnswer,
  leaffySuggestions,
} from "../services/leaffyKnowledge";
import {
  getLeaffyPeriod,
  nextSunshineDelay,
  shouldLeaffyYawn,
  LEAFFY_SUN_MS,
  LEAFFY_YAWN_MS,
} from "../services/leaffyRoutine";
import expressions from "../assets/leaffy-expressions.webp";
import motionFrames from "../assets/leaffy-motion.webp";
import routineFrames from "../assets/leaffy-routine.webp";
import "./LeaffyMascot.css";
import { api } from "../services/api";
import { useTheme } from "../ThemeProvider";

const greetings = [
  "Hi, I’m Leaffy! A little greener together?",
  "A tiny scrap. A fresh start. Ask me how!",
  "Curious about SoilSync? I’m right here!",
];
const welcome = {
  role: "assistant",
  content:
    "Hi, I’m Leaffy! 🌱 Your little leaf companion. Ask me about SoilSync, your food scraps, composting or growing greener habits.",
  source: "welcome",
};

function LeaffySprite({ mood = "happy", waving = false, className = "" }) {
  const routine = ["yawning", "sunbathing", "waking"].includes(mood);
  const animated = mood !== "sleepy" && mood !== "excited" && !routine;
  const sheet = routine ? routineFrames : animated ? motionFrames : expressions;
  return (
    <span
      className={`leaffy-sprite leaffy-sprite-${mood} ${animated ? "leaffy-motion-frames" : ""} ${waving ? "leaffy-waving" : ""} ${className}`}
      style={{ backgroundImage: `url(${sheet})` }}
      aria-hidden="true"
    />
  );
}

export default function LeaffyMascot({ placement = "landing" }) {
  const onBoard = placement === "board";
  const { theme, chooseTheme } = useTheme();
  const [open, setOpen] = useState(false);
  const [resting, setResting] = useState(() => {
    try {
      return sessionStorage.getItem("soilsync-leaffy-resting") === "true";
    } catch {
      return false;
    }
  });
  const [motionAllowed, setMotionAllowed] = useState(false);
  const [interacting, setInteracting] = useState(false);
  const [period, setPeriod] = useState(getLeaffyPeriod);
  const [visible, setVisible] = useState(() => !document.hidden);
  const [animation, setAnimation] = useState("idle");
  const [waking, setWaking] = useState(false);
  const [greeting, setGreeting] = useState("");
  const [messages, setMessages] = useState([welcome]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState(
    "SoilSync guide · ask about your greener routine",
  );
  const dialog = useRef(null),
    launcher = useRef(null),
    input = useRef(null),
    log = useRef(null);
  const alive = useRef(true),
    wakeTimer = useRef(null);
  const replyController = useRef(null);
  const lastGreeting = useRef(0),
    greetingIndex = useRef(0);
  const lastActivity = useRef(Date.now()),
    lastYawn = useRef(0),
    activity = useRef("idle");
  const changeAnimation = useCallback((next) => {
    activity.current = next;
    setAnimation(next);
  }, []);

  useEffect(() => {
    alive.current = true;
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const updateMotion = () => setMotionAllowed(!media.matches);
    const onVisibility = () => {
      setVisible(!document.hidden);
      setPeriod(getLeaffyPeriod());
      if (!document.hidden) lastActivity.current = Date.now();
    };
    const onActivity = () => {
      lastActivity.current = Date.now();
      if (activity.current === "yawning") changeAnimation("idle");
    };
    updateMotion();
    media.addEventListener("change", updateMotion);
    document.addEventListener("visibilitychange", onVisibility);
    const events = ["pointermove", "pointerdown", "keydown", "scroll"];
    events.forEach((event) =>
      window.addEventListener(event, onActivity, { passive: true }),
    );
    const clock = window.setInterval(() => setPeriod(getLeaffyPeriod()), 30000);
    return () => {
      alive.current = false;
      replyController.current?.abort();
      window.clearTimeout(wakeTimer.current);
      window.clearInterval(clock);
      media.removeEventListener("change", updateMotion);
      document.removeEventListener("visibilitychange", onVisibility);
      events.forEach((event) => window.removeEventListener(event, onActivity));
    };
  }, [changeAnimation]);

  useEffect(() => {
    if (open) {
      dialog.current.showModal();
      input.current?.focus();
    } else dialog.current?.close();
  }, [open]);

  useEffect(() => {
    if (!open || !log.current) return;
    log.current.scrollTop = log.current.scrollHeight;
  }, [messages, busy, open]);

  useEffect(() => {
    changeAnimation("idle");
    if (!motionAllowed || resting || period === "night" || open || !visible)
      return;
    let sunshineAt = Date.now() + nextSunshineDelay();
    let finishAt = 0;
    const timer = window.setInterval(() => {
      const now = Date.now();
      if (activity.current !== "idle") {
        if (now < finishAt) return;
        changeAnimation("idle");
      }
      if (interacting) return;
      if (shouldLeaffyYawn(now, lastActivity.current, lastYawn.current)) {
        lastYawn.current = now;
        finishAt = now + LEAFFY_YAWN_MS;
        setGreeting("");
        changeAnimation("yawning");
      } else if (!onBoard && now >= sunshineAt) {
        sunshineAt = now + nextSunshineDelay() + LEAFFY_SUN_MS;
        finishAt = now + LEAFFY_SUN_MS;
        setGreeting("");
        changeAnimation("sunbathing");
      }
    }, 1000);
    return () => window.clearInterval(timer);
  }, [
    motionAllowed,
    resting,
    period,
    open,
    visible,
    interacting,
    changeAnimation,
    onBoard,
  ]);

  useEffect(() => {
    if (!greeting) return;
    const timer = window.setTimeout(() => setGreeting(""), 6000);
    return () => window.clearTimeout(timer);
  }, [greeting]);

  useEffect(() => {
    if (
      !motionAllowed ||
      resting ||
      period === "night" ||
      open ||
      interacting ||
      !visible
    ) {
      setGreeting("");
      return;
    }
    const sayHi = () => {
      if (
        activity.current !== "idle" ||
        Date.now() - lastActivity.current >= 45000 ||
        Date.now() - lastGreeting.current < 44000
      )
        return;
      setGreeting(greetings[greetingIndex.current % greetings.length]);
      greetingIndex.current += 1;
      lastGreeting.current = Date.now();
    };
    const delay = lastGreeting.current
      ? Math.max(3500, 45000 - (Date.now() - lastGreeting.current))
      : 3500;
    const firstHi = window.setTimeout(sayHi, delay);
    const helloTimer = window.setInterval(sayHi, 45000);
    return () => {
      window.clearTimeout(firstHi);
      window.clearInterval(helloTimer);
    };
  }, [motionAllowed, resting, period, open, interacting, visible]);

  const closeChat = () => {
    setOpen(false);
    setWaking(false);
    window.clearTimeout(wakeTimer.current);
    launcher.current?.focus();
  };
  const openChat = () => {
    if (waking || open) return;
    setGreeting("");
    lastActivity.current = Date.now();
    changeAnimation("idle");
    if (period === "night" && motionAllowed && !resting) {
      setWaking(true);
      wakeTimer.current = window.setTimeout(() => {
        if (alive.current) {
          setWaking(false);
          setOpen(true);
        }
      }, 1800);
    } else setOpen(true);
  };
  const toggleRest = () => {
    setGreeting("");
    const next = !resting;
    try {
      sessionStorage.setItem("soilsync-leaffy-resting", String(next));
    } catch {
      /* Session preferences are optional. */
    }
    setResting(next);
  };

  async function send(text) {
    const trimmed = text.trim();
    if (busy || trimmed.length < 3 || trimmed.length > 600) return;
    setQuestion("");
    setGreeting("");
    setBusy(true);
    setStatus("Asking Leaffy…");
    setMessages((current) => [
      ...current.slice(-30),
      { role: "user", content: trimmed },
    ]);
    const controller = new AbortController();
    replyController.current = controller;
    try {
      const reply = await api("/ai/chat", {
        method: "POST",
        body: { question: trimmed },
        signal: controller.signal,
      });
      if (!alive.current || controller.signal.aborted) return;
      setMessages((current) => [
        ...current,
        { role: "assistant", content: reply.answer, source: "gemini" },
      ]);
      setStatus("Gemini reply · review suggestions before acting");
    } catch {
      if (!alive.current || controller.signal.aborted) return;
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: findLeaffyAnswer(trimmed),
          source: "guide",
        },
      ]);
      setStatus("Live AI unavailable · showing the project guide");
    } finally {
      if (alive.current && replyController.current === controller)
        setBusy(false);
    }
  }

  function stopReply() {
    replyController.current?.abort();
    setBusy(false);
    setStatus("Reply stopped. You can ask another question.");
  }
  function clearChat() {
    replyController.current?.abort();
    setBusy(false);
    setMessages([welcome]);
    setQuestion("");
    input.current?.focus();
  }
  const sleeping = (resting || period === "night") && !open && !waking;
  const animated = motionAllowed && visible && !resting;
  const mood = sleeping
    ? "sleepy"
    : waking
      ? "waking"
      : busy
        ? "thinking"
        : animation === "yawning"
          ? "yawning"
          : animation === "sunbathing"
            ? "sunbathing"
            : "happy";
  const routine = sleeping
    ? "sleeping"
    : waking
      ? "waking"
      : open
        ? busy
          ? "thinking"
          : "listening"
        : animation;
  const caption = sleeping
    ? "Leaffy’s asleep. Tap to chat."
    : waking
      ? "Just a little yawn…"
      : animation === "sunbathing"
        ? "Soaking up a little sunshine."
        : animation === "yawning"
          ? "A little leafy yawn…"
          : greeting || "Ask Leaffy about SoilSync.";

  return (
    <div className={`leaffy ${onBoard ? "leaffy-board" : ""}`} data-period={period} data-activity={routine}>
      <div
        className={`leaffy-dock leaffy-fixed ${animated ? "leaffy-animated" : ""} ${sleeping ? "leaffy-sleeping" : ""} ${animation === "sunbathing" && animated ? "leaffy-sunbathing" : ""} ${animation === "yawning" && animated ? "leaffy-yawning" : ""}`}
        onPointerEnter={() => setInteracting(true)}
        onPointerLeave={() => setInteracting(false)}
        onFocusCapture={() => setInteracting(true)}
        onBlurCapture={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget))
            setInteracting(false);
        }}
      >
        {!onBoard && greeting && !sleeping && !open && animated && (
          <button type="button" className="leaffy-greeting" onClick={openChat}>
            {greeting}
          </button>
        )}
        <button
          ref={launcher}
          type="button"
          className="leaffy-launcher"
          aria-label="Ask Leaffy, SoilSync’s AI companion"
          aria-haspopup="dialog"
          aria-expanded={open}
          aria-controls="leaffy-dialog"
          aria-busy={waking}
          title={caption}
          onClick={openChat}
        >
          <span className="leaffy-body">
            <LeaffySprite
              mood={mood}
              waving={Boolean(greeting) && animated && !interacting}
            />
          </span>
          <span className="leaffy-name">
            Ask Leaffy <Leaf size={12} aria-hidden="true" />
          </span>
        </button>
        {animation === "sunbathing" && animated && !open && (
          <span className="leaffy-sun-effects" aria-hidden="true">
            <Sun className="leaffy-little-sun" size={28} />
            <i className="leaffy-sun-ray leaffy-ray-1" />
            <i className="leaffy-sun-ray leaffy-ray-2" />
            <i className="leaffy-sun-ray leaffy-ray-3" />
            {[0, 1, 2, 3].map((index) => (
              <span
                key={index}
                className="leaffy-oxygen"
                style={{ "--bubble-index": index }}
              >
                O₂
              </span>
            ))}
          </span>
        )}
        {sleeping && (
          <span className="leaffy-zzz" aria-hidden="true">
            <span>z</span>
            <span>z</span>
            <span>Z</span>
          </span>
        )}
      </div>
      {!onBoard && <button type="button" className="leaffy-mobile-intro" onClick={openChat}>
        <span className="leaffy-period-icon" aria-hidden="true">
          {period === "night" ? <Moon size={16} /> : <Sun size={16} />}
        </span>
        <span>{caption}</span>
      </button>}
      <dialog
        id="leaffy-dialog"
        ref={dialog}
        className="leaffy-dialog"
        aria-labelledby="leaffy-title"
        aria-describedby="leaffy-description"
        onCancel={(event) => {
          event.preventDefault();
          closeChat();
        }}
      >
        <header className="leaffy-chat-header">
          <LeaffySprite
            mood={waking ? "yawning" : busy ? "thinking" : "curious"}
            className="leaffy-avatar"
          />
          <div>
            <h2 id="leaffy-title">
              Meet Leaffy <span>🌱</span>
            </h2>
            <p id="leaffy-description">Your SoilSync leaf companion</p>
          </div>
          <button
            type="button"
            className="leaffy-icon-button"
            onClick={closeChat}
            aria-label="Close Leaffy chat"
          >
            <X size={21} aria-hidden="true" />
          </button>
        </header>
        <div className="leaffy-chat-status">
          <span />
          <span>{waking ? "Just waking up… I’m listening." : status}</span>
          <button
            type="button"
            className={onBoard ? "leaffy-theme-toggle" : "leaffy-rest"}
            aria-label={
              onBoard
                ? theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
                : resting ? "Resume Leaffy’s animations" : "Pause Leaffy’s animations"
            }
            title={onBoard ? theme === "dark" ? "Switch to light mode" : "Switch to dark mode" : undefined}
            aria-pressed={onBoard ? undefined : resting}
            onClick={onBoard ? () => chooseTheme(theme === "dark" ? "light" : "dark") : toggleRest}
          >
            {(onBoard ? theme === "dark" : resting) ? (
              <Sun size={16} aria-hidden="true" />
            ) : (
              <Moon size={16} aria-hidden="true" />
            )}
          </button>
        </div>
        {onBoard && <p className="leaffy-data-note">Your question is sent to Google Gemini. Chat stays in this screen until you leave or clear it.</p>}
        <div
          ref={log}
          className="leaffy-chat-log"
          role="log"
          aria-label="Conversation with Leaffy"
          aria-live="polite"
          aria-relevant="additions text"
        >
          {messages.map((message, index) => {
            const isReply = message.role === "assistant" && message.source !== "welcome";
            return (
              <article
                key={index}
                className={`leaffy-message leaffy-message-${message.role}${isReply ? " leaffy-message-reply" : ""}`}
                aria-label={message.role === "user" ? "Your question" : isReply ? "Leaffy’s reply" : "Leaffy’s welcome"}
              >
                <span className={`leaffy-speaker${isReply ? " leaffy-reply-start" : ""}`}>
                  {message.role === "user" ? "YOU" : isReply ? "LEAFFY’S REPLY" : "LEAFFY"}
                </span>
                <p>{message.content}</p>
                {message.warnings?.length > 0 && (
                  <ul>
                    {message.warnings.map((warning) => (
                      <li key={warning}>{warning}</li>
                    ))}
                  </ul>
                )}
                {isReply && (
                  <small>
                    {message.source === "guide"
                      ? "From the SoilSync project guide · not an AI reply"
                      : message.source === "scope_guard"
                        ? "SoilSync and home gardening topics"
                        : "Gemini AI · review suggestions before acting"}
                  </small>
                )}
                {isReply && <div className="leaffy-reply-end">End of reply</div>}
              </article>
            );
          })}
          {busy && (
            <div className="leaffy-thinking" role="status">
              <LeaffySprite mood="thinking" className="leaffy-avatar" />
              <p>
                Let me leaf through that…
                <span>Checking your question with Leaffy.</span>
              </p>
            </div>
          )}
        </div>
        {messages.length === 1 && (
          <div className="leaffy-suggestions" aria-label="Suggested questions">
            {leaffySuggestions.map((suggestion) => (
              <button
                type="button"
                key={suggestion}
                onClick={() => send(suggestion)}
                disabled={busy}
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}
        <form
          className="leaffy-composer"
          onSubmit={(event) => {
            event.preventDefault();
            send(question);
          }}
        >
          <label htmlFor="leaffy-question">Ask about SoilSync</label>
          <div className="leaffy-input-row">
            <textarea
              ref={input}
              id="leaffy-question"
              rows={2}
              maxLength={600}
              placeholder="What would you like to know?"
              value={question}
              disabled={busy}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => {
                if (
                  event.key === "Enter" &&
                  !event.shiftKey &&
                  !event.nativeEvent.isComposing
                ) {
                  event.preventDefault();
                  send(question);
                }
              }}
            />
            {busy ? (
              <button
                type="button"
                className="leaffy-send"
                onClick={stopReply}
                aria-label="Stop Leaffy reply"
              >
                <Square size={17} aria-hidden="true" />
              </button>
            ) : (
              <button
                type="submit"
                className="leaffy-send"
                disabled={question.trim().length < 3}
                aria-label="Send question to Leaffy"
              >
                <Send size={19} aria-hidden="true" />
              </button>
            )}
          </div>
          <div className="leaffy-composer-meta">
            <span>{question.length}/600 · Chat earns no EcoPoints</span>
            <button
              type="button"
              onClick={clearChat}
              disabled={busy || messages.length === 1}
            >
              <Trash2 size={13} aria-hidden="true" /> Clear chat
            </button>
          </div>
        </form>
        <footer className="leaffy-chat-footer">
          <span>Small questions. Greener habits.</span>
          <Link to="/scan" onClick={closeChat}>
            Open scanner <ArrowUpRight size={14} aria-hidden="true" />
          </Link>
        </footer>
      </dialog>
    </div>
  );
}
