import { useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

const API_URL = process.env.EXPO_PUBLIC_ABFINI_API_URL;
const API_KEY = process.env.EXPO_PUBLIC_ABFINI_API_KEY;

export default function App() {
  const [message, setMessage] = useState("");
  const [turns, setTurns] = useState([]);
  const [sending, setSending] = useState(false);

  async function sendMessage() {
    const question = message.trim();
    if (!question || sending) return;
    setMessage("");
    setSending(true);
    setTurns((prev) => [...prev, { role: "user", text: question }]);

    if (!API_URL || !API_KEY) {
      setTurns((prev) => [
        ...prev,
        {
          role: "assistant",
          error: true,
          text: "EXPO_PUBLIC_ABFINI_API_URL / EXPO_PUBLIC_ABFINI_API_KEY ne sont pas configurés (voir .env.example).",
        },
      ]);
      setSending(false);
      return;
    }

    try {
      const response = await fetch(`${API_URL.replace(/\/$/, "")}/v1/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${API_KEY}`,
        },
        body: JSON.stringify({ message: question }),
      });
      const body = await response.json();

      if (!response.ok) {
        setTurns((prev) => [
          ...prev,
          { role: "assistant", error: true, text: body.detail || `Erreur ABFINI (HTTP ${response.status})` },
        ]);
      } else {
        setTurns((prev) => [
          ...prev,
          {
            role: "assistant",
            text: body.answer,
            model: body.model,
            sources: body.sources || [],
          },
        ]);
      }
    } catch (err) {
      setTurns((prev) => [
        ...prev,
        { role: "assistant", error: true, text: "Impossible de joindre l'API ABFINI." },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <Text style={styles.title}>ABFINI ∞ — Test</Text>

        <FlatList
          style={styles.flex}
          contentContainerStyle={styles.listContent}
          data={turns}
          keyExtractor={(_, index) => String(index)}
          ListEmptyComponent={
            <Text style={styles.empty}>Pose une question, par exemple : « Qu'est-ce qu'ABFINI ? »</Text>
          }
          renderItem={({ item }) => (
            <View style={[styles.bubble, item.role === "user" ? styles.userBubble : styles.assistantBubble, item.error && styles.errorBubble]}>
              <Text style={item.role === "user" ? styles.userText : styles.assistantText}>{item.text}</Text>
              {item.model ? <Text style={styles.meta}>Modèle : {item.model}</Text> : null}
              {item.sources && item.sources.length > 0 ? (
                <View style={styles.sources}>
                  <Text style={styles.metaTitle}>Sources :</Text>
                  {item.sources.map((source, index) => (
                    <Text key={index} style={styles.meta}>
                      • document={source.document_id} · chunk={source.chunk_index} · similarité={source.similarity.toFixed(3)}
                    </Text>
                  ))}
                </View>
              ) : null}
            </View>
          )}
        />

        <View style={styles.composer}>
          <TextInput
            style={styles.input}
            value={message}
            onChangeText={setMessage}
            placeholder="Écrire un message…"
            multiline
            maxLength={4000}
          />
          <Pressable
            style={[styles.sendButton, sending && styles.sendButtonDisabled]}
            onPress={sendMessage}
            disabled={sending}
          >
            {sending ? <ActivityIndicator color="#08111f" /> : <Text style={styles.sendText}>Envoyer</Text>}
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#0b0d12" },
  flex: { flex: 1 },
  title: {
    color: "#e7e9ee",
    fontSize: 20,
    fontWeight: "700",
    textAlign: "center",
    paddingVertical: 12,
  },
  listContent: { padding: 16, gap: 10, flexGrow: 1 },
  empty: { color: "#9aa1b2", textAlign: "center", marginTop: 40 },
  bubble: { borderRadius: 14, padding: 12, maxWidth: "90%", marginBottom: 10 },
  userBubble: { backgroundColor: "#6ea8fe", alignSelf: "flex-end" },
  assistantBubble: { backgroundColor: "#151822", borderWidth: 1, borderColor: "#262b3a", alignSelf: "flex-start" },
  errorBubble: { borderColor: "#f5657a" },
  userText: { color: "#08111f", fontSize: 15 },
  assistantText: { color: "#e7e9ee", fontSize: 15 },
  meta: { color: "#9aa1b2", fontSize: 12, marginTop: 4 },
  metaTitle: { color: "#9aa1b2", fontSize: 12, marginTop: 6, fontWeight: "600" },
  sources: { marginTop: 4, borderTopWidth: 1, borderTopColor: "#262b3a", paddingTop: 4 },
  composer: {
    flexDirection: "row",
    gap: 8,
    padding: 12,
    borderTopWidth: 1,
    borderTopColor: "#262b3a",
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: "#262b3a",
    borderRadius: 10,
    padding: 10,
    color: "#e7e9ee",
    backgroundColor: "#151822",
    maxHeight: 100,
  },
  sendButton: {
    backgroundColor: "#6ea8fe",
    borderRadius: 10,
    paddingHorizontal: 18,
    justifyContent: "center",
  },
  sendButtonDisabled: { opacity: 0.5 },
  sendText: { color: "#08111f", fontWeight: "700" },
});
