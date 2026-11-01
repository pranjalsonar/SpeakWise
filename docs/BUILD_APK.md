# Build the SpeakWise APK (EAS cloud build, no Android Studio)

The APK is built on Expo's servers from `mobile/`. Profiles live in `mobile/eas.json`;
`preview` produces an installable `.apk`.

## One-time

```powershell
cd D:\madam_project\SpeakWise\mobile
eas login          # your Expo account (same one used for moment_app)
eas init           # links this folder to an Expo project (adds extra.eas.projectId to app.json)
```

## 1. Choose the backend address baked into the APK (optional)

Open `mobile/app.json` and set `expo.extra.backendUrl`:

```json
"extra": { "backendUrl": "https://your-address.trycloudflare.com" }
```

- Laptop + tunnel: the `trycloudflare.com` address changes on every restart, so you can also leave
  this empty and paste the current address in the app under **Profile → Server** instead.
- Cloud deployment (see `DEPLOY_CLOUD.md`): put the fixed `https://…` address here.
- It must be `https://`: release builds block plain `http://`.

## 2. Build

```powershell
cd D:\madam_project\SpeakWise\mobile
eas build --platform android --profile preview
```

- Say **Yes** when asked to generate a new Android keystore (EAS stores it for you).
- The free plan queues builds, so it can take 10–30 minutes. Progress shows in the terminal and at
  https://expo.dev under the project's Builds.
- When it finishes you get a link and a QR code to download the `.apk`.

## 3. Install on the phone

1. Open the link (or scan the QR) on the Vivo / Realme and download the APK.
2. Allow "Install unknown apps" for your browser when Android asks.
3. Install and open **SpeakWise**.

## 4. Run the backend for the demo

```powershell
cd D:\madam_project\SpeakWise\backend
powershell -ExecutionPolicy Bypass -File scripts\start-demo.ps1
```

Copy the printed `https://….trycloudflare.com` address into the app: **Profile → Server →
Save & test connection** (skip this if you baked a working address into `backendUrl`).

## Rebuilding

Change code or assets, then run the build command again. `appVersionSource: remote` lets EAS manage
version codes. Uninstalling the app deletes its local history; installing an update over it keeps it.
