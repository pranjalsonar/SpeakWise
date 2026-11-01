import { useSQLiteContext } from 'expo-sqlite';
import { useEffect, useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { Banner } from '@/components/ui/banner';
import { Button } from '@/components/ui/button';
import { TextField } from '@/components/ui/text-field';
import { APP_TOKEN_KEY, BACKEND_URL_KEY, defaultBackendUrl } from '@/constants/config';
import { Spacing } from '@/constants/theme';
import { getSetting, setSetting } from '@/db/settings';
import { ApiError, checkHealth, getJob } from '@/services/api';

type Status = { tone: 'success' | 'danger' | 'warning'; message: string } | null;

export function ServerSettings() {
  const db = useSQLiteContext();
  const [url, setUrl] = useState('');
  const [token, setToken] = useState('');
  const [status, setStatus] = useState<Status>(null);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    getSetting(db, BACKEND_URL_KEY).then((v) => setUrl(v ?? ''));
    getSetting(db, APP_TOKEN_KEY).then((v) => setToken(v ?? ''));
  }, [db]);

  const saveAndTest = async () => {
    const value = url.trim().replace(/\/+$/, '');
    if (value && !/^https?:\/\/[^\s/]+/i.test(value)) {
      setStatus({ tone: 'danger', message: 'Enter a full address starting with http:// or https://' });
      return;
    }
    await setSetting(db, BACKEND_URL_KEY, value);
    await setSetting(db, APP_TOKEN_KEY, token.trim());
    const backend = { url: value || defaultBackendUrl(), token: token.trim() };
    setTesting(true);
    setStatus(null);
    try {
      const h = await checkHealth(backend);
      if (h.access_key_required) {
        // A made-up job id: 404 means the key was accepted, 401 means it was not.
        await getJob(backend, 'connection-test').catch((e: ApiError) => {
          if (e.code !== 'not_found') throw e;
        });
      }
      const missing = !h.providers.groq && !h.providers.deepgram;
      setStatus(
        missing
          ? { tone: 'warning', message: 'Connected, but the server has no speech API keys configured.' }
          : { tone: 'success', message: `Connected · ${h.articles} articles on the server` }
      );
    } catch (e) {
      setStatus({ tone: 'danger', message: (e as ApiError).message });
    } finally {
      setTesting(false);
    }
  };

  return (
    <View style={styles.wrap}>
      <TextField
        label="Server address"
        optional
        value={url}
        onChangeText={setUrl}
        placeholder={defaultBackendUrl()}
        autoCapitalize="none"
        autoCorrect={false}
        keyboardType="url"
      />
      <ThemedText type="small" themeColor="textSecondary">
        Leave empty to use {defaultBackendUrl()}
      </ThemedText>
      <TextField
        label="Access key"
        optional
        value={token}
        onChangeText={setToken}
        placeholder="Only if the server asks for one"
        autoCapitalize="none"
        autoCorrect={false}
        secureTextEntry
      />
      {status ? <Banner tone={status.tone} message={status.message} /> : null}
      <Button title="Save & test connection" variant="secondary" onPress={saveAndTest} loading={testing} />
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    gap: Spacing.two + 2,
  },
});
