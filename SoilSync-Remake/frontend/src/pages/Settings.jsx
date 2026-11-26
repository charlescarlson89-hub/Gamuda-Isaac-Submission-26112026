import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlarmClock,
  BellRing,
  ChevronRight,
  Gift,
  Info,
  LogOut,
  Moon,
  Monitor,
  Pencil,
  ShieldCheck,
  Sun,
  SunMoon,
  Ticket,
  UserRound,
} from "lucide-react";
import { useSoilSync } from "../state";
import { Badge, Dialog, Heading, PreviewNote } from "../components/UI";
import { figma } from "../data/figma";
import { useTheme } from "../ThemeProvider";

const settings = [
  ["checkin", "Check-in reminder", AlarmClock],
  ["rewards", "Reward received", Gift],
  ["service", "Service notices", BellRing],
  ["claim", "Claim reward reminder", Ticket],
];
export default function Settings({ profile = false }) {
  const { state, act, setNotice, busy } = useSoilSync();
  const { preference, chooseTheme } = useTheme();
  const [dialog, setDialog] = useState(null);
  const [name, setName] = useState(state.profile.name);
  const [location, setLocation] = useState(state.profile.location);
  const navigate = useNavigate();
  return (
    <div className="page-stack settings-page">
      {profile && (
        <div className="page-heading">
          <h1>Your green corner</h1>
          <UserRound size={26} />
        </div>
      )}
      <section className="profile-card">
        <div className="profile-card-main">
          <img src={figma.settings[0].src} alt="Garden profile illustration" />
          <div>
            <h2>
              {state.profile.name} <ShieldCheck size={19} />
            </h2>
            <p>{state.profile.location || "My home garden"}</p>
            <button
              className="text-button"
              onClick={() => {
                setName(state.profile.name);
                setLocation(state.profile.location);
                setDialog("profile");
              }}
            >
              <Pencil size={16} /> Edit Profile
            </button>
          </div>
          <span className="profile-tag">
            SOILSYNC
            <br />
            MEMBER
          </span>
        </div>
        <div className="profile-progress">
          <div className="row-between">
            <span>{state.profile.streakDays || 0} day streak</span>
            <span>Small steps, together</span>
          </div>
          <progress
            value={Math.min(state.profile.streakDays || 0, 7)}
            max={7}
            aria-label="Check-in streak out of seven days"
          />
          <div className="row-between">
            <span>{state.redemptions.length} rewards collected</span>
            <span>{state.batches.length} compost batches</span>
          </div>
        </div>
      </section>
      <Heading icon={BellRing} title="Notification Preferences" />
      <div className="preference-list">
        {settings.map(([key, label, Icon]) => (
          <div className="preference-row" key={key}>
            <span>
              <Icon size={23} />
            </span>
            <label id={`label-${key}`}>{label}</label>
            <button
              type="button"
              role="switch"
              disabled={busy}
              aria-checked={state.preferences[key]}
              aria-labelledby={`label-${key}`}
              className={`toggle ${state.preferences[key] ? "on" : ""}`}
              onClick={() =>
                act({ type: "PREFERENCE", key, value: !state.preferences[key] })
              }
            >
              <i />
            </button>
          </div>
        ))}
        <div className="quiet-hours">
          <Moon size={18} />
          <span>Quiet hours</span>
          <strong>
            {state.quietHours.start} – {state.quietHours.end}
          </strong>
        </div>
        <PreviewNote>
          Preferences are saved to your account. Device notification delivery is
          not enabled yet.
        </PreviewNote>
      </div>
      <section className="appearance-panel" aria-labelledby="appearance-heading">
        <div className="section-heading">
          <h2 id="appearance-heading"><SunMoon size={21} aria-hidden="true" /> Appearance</h2>
        </div>
        <fieldset className="theme-options">
          <legend>Color theme</legend>
          {[["system", "Device", Monitor], ["light", "Light", Sun], ["dark", "Dark", Moon]].map(([value, label, Icon]) => (
            <label key={value}>
              <input type="radio" name="color-theme" value={value}
                checked={preference === value} onChange={() => chooseTheme(value)} />
              <span><Icon size={18} aria-hidden="true" />{label}</span>
            </label>
          ))}
        </fieldset>
        <p className="preview-note">Saved on this device. Device follows your phone’s appearance.</p>
      </section>
      <section className="settings-links">
        <button onClick={() => setDialog("about")}>
          <Info size={22} />
          <span>
            <strong>About SoilSync App</strong>
            <small>A small leaf. A big impact.</small>
          </span>
          <Badge>TEDA BYTE</Badge>
          <ChevronRight size={20} />
        </button>
        <button onClick={() => setDialog("privacy")}>
          <ShieldCheck size={22} />
          <span>
            <strong>Terms & Privacy</strong>
            <small>Your account and data use</small>
          </span>
          <ChevronRight size={20} />
        </button>
      </section>
      <button
        className="button logout-button"
        disabled={busy}
        onClick={async () => {
          if (await act({ type: "SIGNOUT" })) navigate("/login");
        }}
      >
        <LogOut size={21} /> Log Out
      </button>
      <PreviewNote>SoilSync · TEDA BYTE</PreviewNote>
      {dialog && (
        <Dialog
          title={
            dialog === "profile"
              ? "Your household profile"
              : dialog === "about"
                ? "A little about SoilSync"
                : "Terms & Privacy"
          }
          onClose={() => setDialog(null)}
        >
          {dialog === "profile" ? (
            <form
              onSubmit={async (event) => {
                event.preventDefault();
                if (await act({ type: "PROFILE", name, location })) {
                  setDialog(null);
                  setNotice("Your profile is updated.");
                }
              }}
            >
              <label htmlFor="edit-name">Username</label>
              <input
                id="edit-name"
                value={name}
                minLength={3}
                maxLength={40}
                required
                onChange={(event) => setName(event.target.value)}
              />
              <label htmlFor="edit-location">Location</label>
              <input
                id="edit-location"
                value={location}
                maxLength={80}
                required
                onChange={(event) => setLocation(event.target.value)}
              />
              <button className="button" type="submit" disabled={busy}>
                {busy ? "Saving…" : "Save profile"}
              </button>
            </form>
          ) : dialog === "about" ? (
            <>
              <p>
                SoilSync helps households give food scraps a second life through
                composting, learning and greener daily habits.
              </p>
              <p>
                Track separate compost batches, record photo check-ins and
                explore practical eco rewards. Daily check-in earns 10 points, a
                new scan with compostable waste 50, and a completed weekly quest
                100.
              </p>
              <p className="preview-note">
                Partner rewards remain project concepts without real fulfilment.
              </p>
            </>
          ) : (
            <>
              <p>
                Your username, email, location, password hash, activities and
                reward claims are stored with your account. Logging out ends
                this session without deleting your progress.
              </p>
              <p>
                Scan and weekly check-in photos are sent to Google Gemini for
                waste identification or a visible-compost check. Approved
                check-in photos are saved privately. Only the signed-in owner
                can view account photos.
              </p>
              <p>
                You can delete completed batches and their photos. AI results
                and check-ins do not prove compost maturity or nutrient content.
                Reward partners and fulfilment are concepts.
              </p>
              <p>
                This test-project notice needs review before public
                registration. Contact the TEDA BYTE project team through your
                bootcamp channel for account-data requests.
              </p>
            </>
          )}
        </Dialog>
      )}
    </div>
  );
}
