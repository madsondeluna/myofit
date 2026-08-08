/**
 * Garmin Connect sign-in.
 *
 * The password is posted once and never stored: the backend exchanges it for
 * garth OAuth tokens and keeps only those. Accounts with two-factor enabled
 * come back asking for a code, which is submitted as a second call.
 */

import { useEffect, useState } from "react";
import type { GarminStatus } from "../api";
import { api } from "../api";
import { Notice, SectionTitle } from "./AppShell";

export function GarminSettings() {
  const [status, setStatus] = useState<GarminStatus | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mfaCode, setMfaCode] = useState("");
  const [needsMfa, setNeedsMfa] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = () =>
    api
      .garminStatus()
      .then(setStatus)
      .catch((err: Error) => setError(err.message));

  useEffect(() => {
    refresh();
  }, []);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await api.garminLogin({
        email,
        password,
        mfa_code: mfaCode || null,
      });
      setStatus(result);
      if (!result.authenticated) {
        // The backend signals a pending second factor with this prefix rather
        // than a distinct status code, since the request itself succeeded.
        if (result.detail?.startsWith("mfa_required")) {
          setNeedsMfa(true);
          setError("Enter the code Garmin sent you.");
        } else {
          setError(result.detail ?? "Sign in failed");
        }
      } else {
        setNeedsMfa(false);
        setPassword("");
        setMfaCode("");
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const signOut = async () => {
    setBusy(true);
    try {
      setStatus(await api.garminLogout());
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section>
      <SectionTitle>Garmin Connect</SectionTitle>

      {error && <Notice kind="error">{error}</Notice>}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
        <div>
          {status?.authenticated ? (
            <>
              <p className="mb-6">
                Signed in{status.profile_name ? ` as ${status.profile_name}` : ""}.
              </p>
              <button type="button" className="myo-btn" disabled={busy} onClick={signOut}>
                Sign out
              </button>
            </>
          ) : (
            <form onSubmit={submit}>
              <label className="block mb-6">
                <span className="myo-eyebrow block mb-2">Email</span>
                <input
                  className="myo-field"
                  type="email"
                  autoComplete="username"
                  required
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                />
              </label>
              <label className="block mb-6">
                <span className="myo-eyebrow block mb-2">Password</span>
                <input
                  className="myo-field"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />
              </label>
              {needsMfa && (
                <label className="block mb-6">
                  <span className="myo-eyebrow block mb-2">Verification code</span>
                  <input
                    className="myo-field"
                    inputMode="numeric"
                    value={mfaCode}
                    onChange={(event) => setMfaCode(event.target.value)}
                  />
                </label>
              )}
              <button type="submit" className="myo-btn myo-btn-accent" disabled={busy}>
                {busy ? "Signing in" : "Sign in"}
              </button>
            </form>
          )}
        </div>

        <div style={{ maxWidth: "var(--measure-prose, 480px)" }}>
          <p className="myo-eyebrow mb-3">How this works</p>
          <p className="mb-6" style={{ fontSize: "var(--text-13)", color: "var(--muted)" }}>
            The password is sent once to exchange it for session tokens. Only the
            tokens are written to disk, in the directory named by GARMINTOKENS.
            The password itself is never stored.
          </p>
          <p className="myo-eyebrow mb-3">Limitations</p>
          <p style={{ fontSize: "var(--text-13)", color: "var(--muted)" }}>
            Garmin publishes no public workout API. MyoFit uses the same internal
            endpoints the website does, through the garminconnect library, and
            Garmin can change them without notice. When a sync fails, the .FIT
            export still produces a file you can copy to the watch over USB.
          </p>
        </div>
      </div>
    </section>
  );
}
