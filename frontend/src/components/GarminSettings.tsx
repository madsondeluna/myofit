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
          setError("Digite o código que o Garmin enviou.");
        } else {
          setError(result.detail ?? "Falha ao entrar");
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
                Conectado{status.profile_name ? ` como ${status.profile_name}` : ""}.
              </p>
              <button type="button" className="myo-btn" disabled={busy} onClick={signOut}>
                Sair
              </button>
            </>
          ) : (
            <form onSubmit={submit}>
              <label className="block mb-6">
                <span className="myo-eyebrow block mb-2">E-mail</span>
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
                <span className="myo-eyebrow block mb-2">Senha</span>
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
                  <span className="myo-eyebrow block mb-2">Código de verificação</span>
                  <input
                    className="myo-field"
                    inputMode="numeric"
                    value={mfaCode}
                    onChange={(event) => setMfaCode(event.target.value)}
                  />
                </label>
              )}
              <button type="submit" className="myo-btn myo-btn-accent" disabled={busy}>
                {busy ? "Entrando" : "Entrar"}
              </button>
            </form>
          )}
        </div>

        <div style={{ maxWidth: "var(--measure-prose, 480px)" }}>
          <p className="myo-eyebrow mb-3">Como funciona</p>
          <p className="mb-6" style={{ fontSize: "var(--text-13)", color: "var(--muted)" }}>
            A senha é enviada uma vez para trocar por tokens de sessão. Só os
            tokens são gravados em disco, no diretório indicado por
            GARMINTOKENS. A senha em si nunca é armazenada.
          </p>
          <p className="myo-eyebrow mb-3">Limitações</p>
          <p style={{ fontSize: "var(--text-13)", color: "var(--muted)" }}>
            O Garmin não publica API de treinos. O MyoFit usa os mesmos
            endpoints internos do site, pela biblioteca garminconnect, e o
            Garmin pode alterá-los sem aviso. Quando o envio falha, a
            exportação .FIT continua gerando um arquivo que você copia para o
            relógio via USB.
          </p>
        </div>
      </div>
    </section>
  );
}
