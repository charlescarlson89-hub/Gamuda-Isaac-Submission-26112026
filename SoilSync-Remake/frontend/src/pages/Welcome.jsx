import React, { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import {
  ArrowRight,
  Eye,
  EyeOff,
  Leaf,
  LockKeyhole,
  Mail,
  MapPin,
  UserRound,
} from "lucide-react";
import { useSoilSync } from "../state";
import { Dialog, FIcon } from "../components/UI";

export default function Welcome() {
  const { state, authenticate, loading, busy, loadError, refresh } =
    useSoilSync();
  const [mode, setMode] = useState("login");
  const [identifier, setIdentifier] = useState("");
  const [email, setEmail] = useState("");
  const [location, setLocation] = useState("Kota Kinabalu");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const [terms, setTerms] = useState(false);
  const [recovery, setRecovery] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const registering = mode === "register";
  if (!loading && state.profile.id) return <Navigate to="/home" replace />;
  return (
    <main className="welcome-page final-welcome">
      <div className="welcome-brand">
        <span className="welcome-symbol" aria-hidden="true">
          <i />
          <b />
        </span>
        <h1>SoilSync</h1>
      </div>
      <section className="green-loop">
        <div className="section-heading">
          <strong>
            <Leaf size={18} /> YOUR GREEN LOOP
          </strong>
          <small>3 SIMPLE STEPS</small>
        </div>
        <div className="loop-grid">
          {[
            ["Snap scraps", "Identify & learn", 2],
            ["Make fertilizer", "Compost at home", 3],
            ["Grow & earn", "Build better habits", 4],
          ].map(([title, text, index], i) => (
            <div key={title}>
              <span>
                <FIcon page="welcome" index={index} />
              </span>
              <strong>
                {i + 1}. {title}
              </strong>
              <small>{text}</small>
            </div>
          ))}
        </div>
      </section>
      <section className="access-card">
        <div className="section-heading">
          <h2>{registering ? "Create account" : "Log In"}</h2>
          <Leaf size={21} />
        </div>
        <p>A little greener, together. Make yourself at home.</p>
        <div className="category-tabs account-tabs" aria-label="Account access">
          {[
            ["login", "Log In"],
            ["register", "Register"],
          ].map(([key, label]) => (
            <button
              type="button"
              key={key}
              disabled={busy}
              aria-pressed={mode === key}
              className={mode === key ? "selected" : ""}
              onClick={() => {
                setMode(key);
                setPassword("");
                setError("");
              }}
            >
              {label}
            </button>
          ))}
        </div>
        {loadError && (
          <div className="inline-error" role="alert">
            <p>{loadError}</p>
            <button
              className="text-button"
              onClick={() => refresh().catch((err) => setError(err.message))}
            >
              Try again
            </button>
          </div>
        )}
        <form
          onSubmit={async (event) => {
            event.preventDefault();
            setError("");
            try {
              const body = registering
                ? {
                    username: identifier.trim(),
                    email: email.trim(),
                    password,
                    location: location.trim(),
                    accepted_terms: accepted,
                  }
                : { identifier: identifier.trim(), password };
              if (await authenticate(mode, body)) {
                setPassword("");
                navigate("/home");
              }
            } catch (err) {
              setError(err.message);
            }
          }}
        >
          <label htmlFor="household-name">
            {registering ? "Username" : "Name"}
          </label>
          <div className="input-icon">
            <UserRound size={20} />
            <input
              id="household-name"
              autoComplete="username"
              placeholder={
                registering ? "Choose a username" : "Your email or username"
              }
              value={identifier}
              minLength={registering ? 3 : 1}
              maxLength={registering ? 40 : 254}
              required
              onChange={(event) => setIdentifier(event.target.value)}
            />
          </div>
          {registering && (
            <>
              <label htmlFor="household-email">Email</label>
              <div className="input-icon">
                <Mail size={20} />
                <input
                  id="household-email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  maxLength={254}
                  required
                  onChange={(event) => setEmail(event.target.value)}
                />
              </div>
            </>
          )}
          <label htmlFor="household-password">Password</label>
          <div className="input-icon password-input">
            <LockKeyhole size={20} aria-hidden="true" />
            <input
              id="household-password"
              type={showPassword ? "text" : "password"}
              autoComplete={registering ? "new-password" : "current-password"}
              placeholder={
                registering ? "At least 12 characters" : "Enter your password"
              }
              value={password}
              minLength={registering ? 12 : 1}
              maxLength={128}
              required
              onChange={(event) => setPassword(event.target.value)}
            />
            <button
              type="button"
              className="password-toggle"
              aria-label={showPassword ? "Hide password" : "Show password"}
              aria-pressed={showPassword}
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
            </button>
          </div>
          {registering && (
            <>
              <label htmlFor="household-location">Location</label>
              <div className="input-icon">
                <MapPin size={20} />
                <input
                  id="household-location"
                  value={location}
                  maxLength={80}
                  autoComplete="address-level2"
                  required
                  onChange={(event) => setLocation(event.target.value)}
                />
              </div>
              <div className="terms-consent">
                <label>
                  <input
                    type="checkbox"
                    checked={accepted}
                    required
                    onChange={(event) => setAccepted(event.target.checked)}
                  />
                  <span>
                    I have read and accept the terms and data-use notice.
                  </span>
                </label>
                <button
                  type="button"
                  className="text-button"
                  onClick={() => setTerms(true)}
                >
                  Read terms and data use
                </button>
              </div>
            </>
          )}
          {error && (
            <p className="inline-error" role="alert">
              {error}
            </p>
          )}
          <button
            className="button button-brown"
            type="submit"
            disabled={busy || loading}
          >
            {busy ? "Please wait…" : registering ? "Create account" : "Log In"}
            <ArrowRight size={21} />
          </button>
        </form>
        {!registering && (
          <button
            type="button"
            className="forgot-password"
            onClick={() => setRecovery(true)}
          >
            Forgot password?
          </button>
        )}
        <div className="welcome-divider">
          <span>Your first green step</span>
        </div>
        <p className="preview-note">
          Your profile and progress belong to your account. Passwords are
          securely hashed.
        </p>
      </section>
      <footer className="welcome-footer">
        <span>
          <i /> A small leaf. A big impact.
        </span>
        <span>TEDA BYTE</span>
      </footer>
      {recovery && (
        <Dialog
          title="Forgot your password?"
          onClose={() => setRecovery(false)}
        >
          <p>
            Contact the TEDA BYTE project administrator to recover your account.
            Email password recovery is not connected yet.
          </p>
          <p>
            Keep your password private. Your compost batches and points are
            preserved during account recovery.
          </p>
          <button className="button" onClick={() => setRecovery(false)}>
            Back to log in
          </button>
        </Dialog>
      )}
      {terms && (
        <Dialog
          title="Terms and data-use notice"
          onClose={() => setTerms(false)}
        >
          <p>
            <strong>SoilSync test project · 20 October 2026</strong>
          </p>
          <p>
            SoilSync is a TEDA BYTE project for learning about food waste and
            home composting. Registration stores your username, email, location,
            a password hash and your acceptance of this notice.
          </p>
          <p>
            Your account records include check-ins, points, scans, batches and
            reward claims. Scan and weekly proof photos are sent to Google
            Gemini to identify waste or check for visible compost. Approved
            weekly proof photos are stored privately. Do not upload faces,
            documents or other personal information.
          </p>
          <p>
            AI results can be wrong. Review identified materials before
            composting. Check-ins do not verify compost maturity or nutrient
            content. Points and partner rewards are project concepts, not cash
            or confirmed partner vouchers.
          </p>
          <p>
            You can delete completed batches and their photos. Contact the
            project team through your bootcamp project channel for account-data
            requests. This notice is a test-project draft and needs review
            before public registration is launched.
          </p>
          <button className="button" onClick={() => setTerms(false)}>
            Back to registration
          </button>
        </Dialog>
      )}
    </main>
  );
}
