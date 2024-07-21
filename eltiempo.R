# Cargar librerías necesarias
library(rtweet)
library(tidyverse)
library(tidytext)
library(waffle)
library(tm)
library(stopwords)
library(wordcloud)
library(wordcloud2)
library(syuzhet)
library(stringi)
library(parallel)
library(udpipe)
library(kableExtra)
library(knitr)
library(lubridate)
library(plotly)
library(ggrepel)
library(readxl)
library(writexl)
library(openxlsx)

# Cargar los datos desde el archivo Excel
datos <- read_excel("articulos_eltiempo.xlsx")

# Limpieza del texto principal
datos <- datos %>%
  mutate(text = str_replace_all(text, "https\\S*", "")) %>%
  mutate(text = str_replace_all(text, "@\\S*", "")) %>%
  mutate(text = str_replace_all(text, "[\r\n\t]", "")) %>%
  mutate(text = removeNumbers(text)) %>%
  mutate(text = removePunctuation(text)) %>%
  mutate(text = str_squish(text))

# Limpieza de los comentarios
datos <- datos %>%
  mutate(comments_clean = str_replace_all(coments, "https\\S*", "")) %>%
  mutate(comments_clean = str_replace_all(comments_clean, "@\\S*", "")) %>%
  mutate(comments_clean = str_replace_all(comments_clean, "[\r\n\t]", "")) %>%
  mutate(comments_clean = removeNumbers(comments_clean)) %>%
  mutate(comments_clean = removePunctuation(comments_clean)) %>%
  mutate(comments_clean = str_squish(comments_clean))

# Palabras vacías
stpwSnow <- stopwords(language = "es", source = "snowball")
stpwIso <- stopwords(language = "es", source = "stopwords-iso")
stpwNtlk <- stopwords(language = "es", source = "nltk")
stpwNtlkEn <- stopwords(language = "en", source = "nltk")

# Conteo de palabras en el texto principal
misdatos <- datos %>%
  select(text) %>%
  unnest_tokens(token, text, to_lower = F)
misdatos <- misdatos %>%
  filter(!token %in% c(stpwNtlk)) %>%
  filter(!token %in% c(stpwNtlkEn))

# Descargar modelo pre entrenado-UDPIPE
# udpipe::udpipe_download_model('spanish') 
theModel <- udpipe_load_model("spanish-gsd-ud-2.5-191206.udpipe")
tweetsAnn <- as_tibble(udpipe_annotate(theModel, misdatos$token))

# Stemming
misdatos <- tweetsAnn %>%
  select(token, lemma) %>%
  filter(!is.na(lemma))
misdatos <- subset(misdatos, token != "RT")

# Conteo de palabras (nuevamente)
misdatos <- misdatos %>%
  mutate(lemma = tolower(lemma)) %>%
  filter(!lemma %in% c(stpwNtlk)) %>%
  filter(!lemma %in% c(stpwNtlkEn))

library(openxlsx)

# Guardar el data frame como un archivo Excel
write.xlsx(misdatos, file = "misdatos4.xlsx")

grafico <- misdatos %>% 
  count(lemma, sort = TRUE) %>%
  top_n(30) %>%
  mutate(lemma = reorder(lemma, n)) %>%
  ggplot(aes(x = lemma, y = n)) +
  geom_col(aes(fill = n)) +
  xlab(NULL) +
  coord_flip() +
  labs(y = "Count",
       x = "Palabras",
       title = "Pruebas de noticias - Textos",
       subtitle = "Top 30 palabras más usadas en textos") +
  geom_text(aes(label = n), size = 3, hjust = 1.5, color = "white")

ggsave("grafico.png",grafico)

# Conteo de palabras en los comentarios
coments_data <- datos %>%
  select(comments_clean) %>%
  unnest_tokens(token, comments_clean, to_lower = F)
coments_data <- coments_data %>%
  filter(!token %in% c(stpwNtlk)) %>%
  filter(!token %in% c(stpwNtlkEn))

comentsAnn <- as_tibble(udpipe_annotate(theModel, coments_data$token))

# Stemming en los comentarios
coments_data <- comentsAnn %>%
  select(token, lemma) %>%
  filter(!is.na(lemma))
coments_data <- subset(coments_data, token != "RT")

# Conteo de palabras (nuevamente) en los comentarios
coments_data <- coments_data %>%
  mutate(lemma = tolower(lemma)) %>%
  filter(!lemma %in% c(stpwNtlk)) %>%
  filter(!lemma %in% c(stpwNtlkEn))

coments_data %>% 
  count(lemma, sort = TRUE) %>%
  top_n(30) %>%
  mutate(lemma = reorder(lemma, n)) %>%
  ggplot(aes(x = lemma, y = n)) +
  geom_col(aes(fill = n)) +
  xlab(NULL) +
  coord_flip() +
  labs(y = "Count",
       x = "Palabras",
       title = "Pruebas de noticias - Textos",
       subtitle = "Top 30 palabras más usadas en textos") +
  geom_text(aes(label = n), size = 3, hjust = 1.5, color = "white")

# Análisis de sentimiento en el texto principal
cl <- makeCluster(detectCores() - 1)
clusterExport(cl = cl, c("get_sentiment", "get_sent_values", "get_nrc_sentiment", 
                         "get_nrc_values", "parLapply"))
tweetSentimentNRC <- get_nrc_sentiment(misdatos$lemma, language = "spanish", cl = cl)
stopCluster(cl)

# Análisis de sentimiento en los comentarios
cl <- makeCluster(detectCores() - 1)
clusterExport(cl = cl, c("get_sentiment", "get_sent_values", "get_nrc_sentiment", 
                         "get_nrc_values", "parLapply"))
commentsSentimentNRC <- get_nrc_sentiment(coments_data$lemma, language = "spanish", cl = cl)
stopCluster(cl)

# Etiquetado del texto principal
tweetSentimentNRC <- cbind(misdatos, tweetSentimentNRC)

# Etiquetado de los comentarios
commentsSentimentNRC <- cbind(coments_data, commentsSentimentNRC)

# Contar palabras por sentimiento en el texto principal
sentiment_word_counts <- tweetSentimentNRC %>%
  select(token, lemma, starts_with("negative"), starts_with("positive"), starts_with("anger"), 
         starts_with("anticipation"), starts_with("disgust"), starts_with("fear"), 
         starts_with("joy"), starts_with("sadness"), starts_with("surprise"), 
         starts_with("trust")) %>%
  pivot_longer(cols = starts_with("negative"):starts_with("trust"),
               names_to = "sentiment",
               values_to = "value") %>%
  filter(value > 0) %>%
  group_by(sentiment, lemma) %>%
  summarize(count = n(), .groups = "drop")

# Contar palabras por sentimiento en los comentarios
sentiment_word_counts_comments <- commentsSentimentNRC %>%
  select(token, lemma, starts_with("negative"), starts_with("positive"), starts_with("anger"), 
         starts_with("anticipation"), starts_with("disgust"), starts_with("fear"), 
         starts_with("joy"), starts_with("sadness"), starts_with("surprise"), 
         starts_with("trust")) %>%
  pivot_longer(cols = starts_with("negative"):starts_with("trust"),
               names_to = "sentiment",
               values_to = "value") %>%
  filter(value > 0) %>%
  group_by(sentiment, lemma) %>%
  summarize(count = n(), .groups = "drop")

# Mostrar palabras negativas del texto principal
negative_words_text <- sentiment_word_counts %>%
  filter(sentiment == "negative") %>%
  arrange(desc(count)) %>%
  head(20)

# Mostrar palabras negativas de los comentarios
negative_words_comments <- sentiment_word_counts_comments %>%
  filter(sentiment == "negative") %>%
  arrange(desc(count)) %>%
  head(20)

# Imprimir palabras negativas de los comentarios
print(negative_words_comments)

# Gráfico de sentimiento del texto principal
sentimentScores <- data.frame(colSums(tweetSentimentNRC %>% 
                                        filter(lemma != "general") %>% 
                                        select(-token, -lemma)))
names(sentimentScores) <- "Score"
sentimentScores <- cbind("sentiment" = rownames(sentimentScores), sentimentScores)
sentimentScores <- sentimentScores
ggplot(data = sentimentScores, aes(x = sentiment, y = Score)) +
  geom_bar(aes(fill = sentiment), stat = "identity") +
  xlab("Sentimientos") + ylab("Score") +
  ggtitle("¿Cuáles son los sentimientos para la búsqueda de noticias?", 
          "Sentimientos basados en Score") +
  theme(axis.text.x = element_text(angle = 45),
        legend.position = "none")

# Gráfico de sentimiento de los comentarios
sentimentScores_comments <- data.frame(colSums(commentsSentimentNRC %>% 
                                                 filter(lemma != "general") %>% 
                                                 select(-token, -lemma)))
names(sentimentScores_comments) <- "Score"
sentimentScores_comments <- cbind("sentiment" = rownames(sentimentScores_comments), sentimentScores_comments)
sentimentScores_comments <- sentimentScores_comments
ggplot(data = sentimentScores_comments, aes(x = sentiment, y = Score)) +
  geom_bar(aes(fill = sentiment), stat = "identity") +
  xlab("Sentimientos") + ylab("Score") +
  ggtitle("¿Cuáles son los sentimientos en los comentarios de las noticias?", 
          "Sentimientos basados en Score") +
  theme(axis.text.x = element_text(angle = 45),
        legend.position = "none")

# Nube de palabras más usadas en textos
misdatos %>% 
  filter(lemma != "im", lemma != "w", lemma != "pm") %>%
  count(lemma, sort = TRUE) %>%
  mutate(lemma = reorder(lemma, n)) %>%
  select(word = lemma, freq = n) %>% 
  wordcloud2()

# Nube de palabras más usadas en comentarios
coments_data %>% 
  filter(lemma != "im", lemma != "w", lemma != "pm", lemma != "n") %>%
  count(lemma, sort = TRUE) %>%
  mutate(lemma = reorder(lemma, n)) %>%
  select(word = lemma, freq = n) %>% 
  wordcloud2()

# Filtrar palabras negativas para texto principal
negative_words_text <- sentiment_word_counts %>%
  filter(sentiment == "negative") %>%
  arrange(desc(count))

# Filtrar palabras negativas para comentarios
negative_words_comments <- sentiment_word_counts_comments %>%
  filter(sentiment == "negative") %>%
  arrange(desc(count))

# Preparar datos para wordcloud2 para palabras negativas del texto principal
wordcloud_data_text <- negative_words_text %>%
  select(word = lemma, freq = count)

# Preparar datos para wordcloud2 para palabras negativas de los comentarios
wordcloud_data_comments <- negative_words_comments %>%
  select(word = lemma, freq = count)

# Generar la nube de palabras para palabras negativas del texto principal
wordcloud2(wordcloud_data_text, color = 'red', backgroundColor = 'white')

# Generar la nube de palabras para palabras negativas de los comentarios
wordcloud2(wordcloud_data_comments, color = 'red', backgroundColor = 'white')

# Guardar el dataframe 'misdatos'
write.xlsx(misdatos, file = "contenido.xlsx")

# Guardar el dataframe 'coments_data'
write.xlsx(coments_data, file = "comentarios.xlsx")

# Guardar el dataframe 'tweetSentimentNRC'
write.xlsx(tweetSentimentNRC, file = "sentimientoscontenido.xlsx")

# Guardar el dataframe 'commentsSentimentNRC'
write.xlsx(commentsSentimentNRC, file = "sentimientocomentarios.xlsx")

# Guardar el dataframe 'sentiment_word_counts' para el texto principal
write.xlsx(sentiment_word_counts, file = "sentiment_word_counts_text.xlsx")

# Guardar el dataframe 'sentiment_word_counts_comments' para los comentarios
write.xlsx(sentiment_word_counts_comments, file = "sentiment_word_counts_comments.xlsx")

# Guardar el dataframe 'negative_words_text' para palabras negativas del texto principal
write.xlsx(negative_words_text, file = "negative_words_text.xlsx")

# Guardar el dataframe 'negative_words_comments' para palabras negativas de los comentarios
write.xlsx(negative_words_comments, file = "negative_words_comments.xlsx")
