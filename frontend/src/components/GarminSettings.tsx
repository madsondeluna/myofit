/**
 * Garmin Connect sign-in.
 *
 * Two ways in, because Garmin offers no third-party authorisation flow. There
 * is no "connect with Garmin" button to build: the developer programme covers
 * the Health API under an approved agreement and does not reach the workout
 * service, and the endpoints MyoFit uses are the ones the mobile app calls,
 * which authenticate with an email and a password over SSO.
 *
 * So either the credentials are entered here and exchanged for tokens that
 * alone are stored, or a token issued elsewhere is pasted in and adopted, and
 * no password ever reaches MyoFit.
 */

import { useEffect, useState } from "react";
import type { GarminStatus } from "../api";
import { api } from "../api";
import { Notice, SectionTitle } from "./AppShell";

type Method = "token" | "password";

export function GarminSettings() {
  const [status, setStatus] = useState<GarminStatus | null>(null);
  const [method, setMethod] = useState<Method>("token");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mfaCode, setMfaCode] = useState("");
  const [needsMfa, setNeedsMfa] = useState(false);
  const [token, setToken] = useState("");
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

  const submitPassword = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await api.garminLogin({ email, password, mfa_code: mfaCode || null });
      setStatus(result);
      if (!result.authenticated) {
        // A pending second factor is signalled with this prefix rather than a
        // distinct status code, since the request itself succeeded.
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

  const submitToken = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await api.garminToken(token);
      setStatus(result);
      if (result.authenticated) setToken("");
      else setError(result.detail ?? "Token recusado");
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
      setError(null);
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

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        <div className="lg:col-span-7">
          {status?.authenticated ? (
            <div className="card-glass glass-lift myo-card p-6">
              <p className="mb-6">
                Conectado{status.profile_name ? ` como ${status.profile_name}` : ""}.
              </p>
              <button type="button" className="pill glass-lift" disabled={busy} onClick={signOut}>
                Desconectar
              </button>
            </div>
          ) : (
            <>
              <div className="myo-rail mb-12">
                <button
                  type="button"
                  className="pill glass-lift"
                  aria-pressed={method === "token"}
                  onClick={() => setMethod("token")}
                >
                  Colar token
                </button>
                <button
                  type="button"
                  className="pill glass-lift"
                  aria-pressed={method === "password"}
                  onClick={() => setMethod("password")}
                >
                  E-mail e senha
                </button>
              </div>

              {method === "token" ? (
                <form onSubmit={submitToken} className="card-glass glass-lift myo-card p-6">
                  <label className="myo-label mb-6">
                    <span className="eyebrow">Token do Garmin</span>
                    <textarea
                      className="glass glass-frost glass-sq myo-field"
                      rows={5}
                      required
                      value={token}
                      onChange={(event) => setToken(event.target.value)}
                    />
                  </label>
                  <button type="submit" className="pill glass-lift pill-primary" disabled={busy}>
                    {busy ? "Conectando" : "Conectar"}
                  </button>
                </form>
              ) : (
                <form onSubmit={submitPassword} className="card-glass glass-lift myo-card p-6">
                  <label className="myo-label mb-6">
                    <span className="eyebrow">E-mail</span>
                    <input
                      className="glass glass-frost glass-sq myo-field"
                      type="email"
                      autoComplete="username"
                      required
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                    />
                  </label>
                  <label className="myo-label mb-6">
                    <span className="eyebrow">Senha</span>
                    <input
                      className="glass glass-frost glass-sq myo-field"
                      type="password"
                      autoComplete="current-password"
                      required
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                    />
                  </label>
                  {needsMfa && (
                    <label className="myo-label mb-6">
                      <span className="eyebrow">Código de verificação</span>
                      <input
                        className="glass glass-frost glass-sq myo-field"
                        inputMode="numeric"
                        value={mfaCode}
                        onChange={(event) => setMfaCode(event.target.value)}
                      />
                    </label>
                  )}
                  <button type="submit" className="pill glass-lift pill-primary" disabled={busy}>
                    {busy ? "Entrando" : "Entrar"}
                  </button>
                </form>
              )}
            </>
          )}
        </div>

        <div
          className="card-glass glass-lift myo-card lg:col-span-4 lg:col-start-9 p-6 self-start"
          style={{ maxWidth: "var(--measure-prose)" }}
        >
          <p className="eyebrow mb-3">Por que não existe botão do Garmin</p>
          <p className="prose prose-justify mb-6" style={{ fontSize: "var(--text-13)" }}>
            O Garmin não publica autorização para aplicativos de terceiros nas
            contas de consumidor. O programa de desenvolvedor cobre a Health
            API, mediante contrato aprovado, e não alcança o serviço de treinos.
            Os endpoints que o MyoFit usa são os mesmos do aplicativo, e eles
            autenticam por e-mail e senha. Não há para onde um botão redirecionar.
          </p>
          <p className="eyebrow mb-3">Colar token</p>
          <p className="prose prose-justify mb-6" style={{ fontSize: "var(--text-13)" }}>
            Autentique onde você já confia e cole aqui o token resultante. O
            MyoFit guarda esse token do mesmo jeito que guardaria um obtido por
            ele, e a senha nunca passa por aqui.
          </p>
          <p className="eyebrow mb-3">E-mail e senha</p>
          <p className="prose prose-justify mb-6" style={{ fontSize: "var(--text-13)" }}>
            A senha é enviada uma vez para trocar por tokens de sessão. Só os
            tokens vão para o disco, no diretório indicado por GARMINTOKENS. A
            senha em si nunca é armazenada.
          </p>
          <p className="eyebrow mb-3">Limitações</p>
          <p className="prose prose-justify" style={{ fontSize: "var(--text-13)" }}>
            Como a API é interna, o Garmin pode alterá-la sem aviso. Quando o
            envio falha, a exportação .FIT continua gerando um arquivo que você
            copia para o relógio via USB.
          </p>
        </div>
      </div>
    </section>
  );
}
