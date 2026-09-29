// One id per browser tab, shared by the realtime socket and diagram saves, so the tab can
// recognise the echo of its own changes when the server pushes them back.
export const TAB_CLIENT_ID = crypto.randomUUID()
