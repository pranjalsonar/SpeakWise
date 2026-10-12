// Narrow, typed bridge to the main process. No filesystem, shell or raw IPC access is exposed.
const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('speakwise', {
  connectionStatus: () => ipcRenderer.invoke('connection:status'),
  signIn: () => ipcRenderer.invoke('connection:signIn'),
  signOut: () => ipcRenderer.invoke('connection:signOut'),
  openNotebook: () => ipcRenderer.invoke('connection:openNotebook'),
  startSession: (input) => ipcRenderer.invoke('session:start', input),
  saveRecording: (sessionId, bytes, mimeType) => ipcRenderer.invoke('session:saveRecording', sessionId, bytes, mimeType),
  submit: (sessionId) => ipcRenderer.invoke('session:submit', sessionId),
  poll: (sessionId) => ipcRenderer.invoke('session:poll', sessionId),
  importReport: (sessionId) => ipcRenderer.invoke('session:importReport', sessionId),
  finish: (sessionId) => ipcRenderer.invoke('session:finish', sessionId),
})
