# Epitteto, Diatribe

Sito trilingue generato con Quarto e pubblicato da GitHub Pages: la traduzione
**italiana** (l'edizione principale), la traduzione **inglese** di
George Long e il **testo greco** di Schenkl. Le tre edizioni hanno le stesse
pagine e le bandierine in alto passano dall'una all'altra restando sulla stessa
diatriba.

La build del sito e del PDF si esegue con `run.bat`.

`run.bat` è **incrementale**: renderizza solo le pagine toccate da un
cambiamento (una correzione a una diatriba già tradotta ⇒ una sola pagina). Gli
hash dei file generati stanno in `.render-cache.json` (non versionato). Forzano
un render completo: `run.bat --full`, la cancellazione di `.render-cache.json`, un
cambio di `styles.css` / `assets/` / `_quarto.yml` / titoli, o un aggiornamento di
Quarto. Prima di pubblicare conviene un `run.bat --full` e un controllo di
`git diff docs/`.

## Com'è fatto il libro

Quattro libri di diatribe, più la lettera con cui Arriano dedica la raccolta a
Lucio Gellio (che nelle fonti è il "libro 0"):

| Libro | Diatribe |
|------:|---------:|
| Lettera di Arriano | 1 |
| I | 30 |
| II | 26 |
| III | 26 |
| IV | 13 |

Ogni diatriba è una pagina; dentro, le sezioni numerate dell'edizione greca
(2641 in tutto) sono l'unità di riferimento canonica, quella con cui il testo si
cita ovunque (I 1, 7 e così via). La traduzione inglese di Long non ha numeri di
sezione — solo i suoi paragrafi, lunghi — e viene quindi mostrata com'è, con le
sue note a piè di pagina in fondo alla pagina.

## Correggere il testo italiano

La traduzione sta in `translation/it/`, **un file Markdown per diatriba**
(`1-01.md` è il libro I, diatriba 1). Ogni file contiene il greco di riferimento
e il corrispondente testo italiano:

```markdown
## 1.1.1

> τῶν ἄλλων δυνάμεων οὐδεμίαν εὑρήσετε αὐτὴν αὑτῆς θεωρητικήν…

Delle altre facoltà non ne troverete nessuna capace di osservare sé stessa…
```

Tre regole e basta:

- `## libro.diatriba.sezione` apre una sezione;
- le righe che cominciano con `>` sono il greco, solo di riferimento, e non
  finiscono nel sito;
- tutto il resto è l'italiano.

Nel testo e nel titolo si può usare `_corsivo_`. Da evitare invece di cominciare
una riga con `>` o con `##`, che sono i due segni riservati.

Per una correzione futura si modifica direttamente il testo sotto la sezione
interessata, oppure il campo `titolo:` nel front matter. Non si devono modificare
i file in `it/`: sono output generati e `run.bat` li sovrascrive. Durante la
build un controllo blocca la generazione se manca un titolo o una sezione.

## Il PDF

Il libro scaricabile esiste **solo in italiano** (il greco e l'inglese sono già
pubblicati altrove) e usa la copertina `data/cover.png` con titolo e autore
composti sopra. Comprende tutte le diatribe. La lettera di Arriano resta fuori
dal PDF, come resta fuori dalle schede della home page: è dedicatoria, non
diatriba, e sul sito basta la voce di menù.

## I file

```
sources/                le due edizioni Perseus in TEI XML (non si toccano)
data/discourses.json    generato: testo greco e inglese già pronti per il sito
data/intro.json         nota introduttiva delle home page, una per lingua
data/credits.json       pagina "Fonti e crediti", una per lingua
data/cover.png          copertina a piena risoluzione (usata dal PDF)
data/cover-web.jpg      la stessa, ridotta e compressa, per il sito
data/flags/             it.png, en.png, grc.png
translation/it/         LA TRADUZIONE ITALIANA (i file da modificare)
tools/site_config.py    lingue, testi dell'interfaccia, URL del sito
tools/0_parse_tei.py    TEI  -> data/discourses.json
tools/1_validate_...    verifica che testo e titoli italiani siano completi
tools/2_generate_site.py  scrive _quarto.yml, index.qmd, it/, en/, grc/
tools/3_generate_pdf_book.py  scrive pdf_book_it.qmd
tools/4_finalize_seo.py   controlli e sitemap dopo il render
tools/5_render.py         render incrementale (sostituisce "quarto render")
tools/_io.py              scrittura idempotente e hashing per i generatori
styles.css              tutto l'aspetto grafico (palette teal)
docs/                   il sito costruito, quello che GitHub Pages pubblica
```

I file `.qmd`, `_quarto.yml`, `lang-config.html` e `pdf_book_it.qmd` sono
**generati**: modificarli a mano non serve, li riscrive `run.bat`. Per correggere
la traduzione si interviene soltanto in `translation/it/`; per gli altri
contenuti si usano i tre file in `data/*.json`, `tools/site_config.py` e
`styles.css`.

## Fonti e licenza

- Testo greco: *Epicteti dissertationes ab Arriano digestae*, ed. Heinrich
  Schenkl, Teubner 1916 — Perseus Digital Library,
  `urn:cts:greekLit:tlg0557.tlg001.perseus-grc2`.
- Traduzione inglese: George Long, *The Discourses of Epictetus*, London 1890 —
  Perseus Digital Library, `urn:cts:greekLit:tlg0557.tlg001.perseus-eng3`.

Entrambi sono distribuiti da Perseus con licenza
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/): il sito li
ripubblica alle stesse condizioni, con la citazione della fonte nella pagina
"Fonti e crediti" e nel PDF.

## Pubblicazione e indicizzazione

- L'URL del sito è in `tools/site_config.py` (`SITE_URL`): va allineato al nome
  del repository prima della prima build pubblica, altrimenti i link canonici e
  la sitemap puntano altrove.
- In Google Search Console aggiungere la proprietà con prefisso URL. Per la
  verifica HTML copiare **solo il codice** fornito da Google in
  `GOOGLE_SITE_VERIFICATION` (in `tools/site_config.py`) ed eseguire `run.bat`:
  finché la variabile è vuota il tag non viene scritto.
- Le statistiche GoatCounter si attivano mettendo il codice del sito in
  `GOATCOUNTER` (per la Bhagavad Gita è `gita`). Finché è vuoto non viene
  caricato nessuno script esterno.
- La sitemap è pubblicata in `<SITE_URL>sitemap.xml` e va inviata in Search
  Console.

### Nota su `robots.txt`

Se il sito è pubblicato come *project site* sotto `/<repo>/`, un `robots.txt` in
questo repository viene servito come `https://<utente>.github.io/<repo>/robots.txt`
e **non** vale per l'host. L'unico file efficace è
`https://<utente>.github.io/robots.txt`, che sta nel repository del sito utente.
