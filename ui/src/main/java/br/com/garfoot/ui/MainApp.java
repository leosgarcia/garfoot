package br.com.garfoot.ui;

import javafx.application.Application;
import javafx.fxml.FXMLLoader;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.stage.Stage;
import javafx.scene.control.*;
import javafx.scene.layout.*;
import javafx.geometry.Insets;
import jakarta.persistence.EntityManagerFactory;

import br.com.garfoot.core.application.usecase.AtualizarClassificacao;
import br.com.garfoot.core.application.usecase.AvancarRodada;
import br.com.garfoot.core.application.usecase.SimularPartida;
import br.com.garfoot.core.application.usecase.CarregarTemporada;
import br.com.garfoot.core.application.usecase.SalvarTemporada;
import br.com.garfoot.core.engine.ForcaEquipe;
import br.com.garfoot.core.engine.MotorCampeonato;
import br.com.garfoot.core.engine.MotorSimulacaoPartida;
import br.com.garfoot.core.model.campeonato.Campeonato;
import br.com.garfoot.core.model.campeonato.TipoCompeticao;
import br.com.garfoot.core.model.clube.Clube;
import br.com.garfoot.core.model.clube.Tecnico;
import br.com.garfoot.core.model.jogador.AtributosJogador;
import br.com.garfoot.core.model.jogador.Jogador;
import br.com.garfoot.core.model.jogador.Posicao;
import br.com.garfoot.core.model.tatica.Formacao;
import br.com.garfoot.core.model.tatica.Escalacao;
import br.com.garfoot.core.model.tatica.Tatica;
import br.com.garfoot.core.model.tatica.EstiloJogo;
import br.com.garfoot.core.service.GeradorRatingJogador;
import br.com.garfoot.core.model.jogador.DadosRatingJogador;
import br.com.garfoot.core.model.jogador.RatingJogador;
import br.com.garfoot.persistence.FabricaPersistencia;
import br.com.garfoot.persistence.repository.RepositorioTemporadaJpa;
import br.com.garfoot.ui.controller.VisaoClubeController;
import br.com.garfoot.ui.presentation.VisaoClubePresenter;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDate;
import java.time.Period;
import java.util.*;
import java.io.InputStream;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;

public final class MainApp extends Application {
    @Override
    public void start(Stage stage) throws Exception {
        EntityManagerFactory fabrica = FabricaPersistencia.criar();
        RepositorioTemporadaJpa repositorio = new RepositorioTemporadaJpa(fabrica);
        this.fabrica = fabrica;
        this.repositorio = repositorio;
        stage.setTitle("Garfoot");
        this.stage = stage;
        telaSplash();
        stage.setOnHidden(event -> {
            if (temporadaAtiva != null) new SalvarTemporada(repositorio).executar(temporadaAtiva);
            fabrica.close();
        });
        stage.show();
    }

    private EntityManagerFactory fabrica;
    private RepositorioTemporadaJpa repositorio;
    private Stage stage;
    private Campeonato temporadaAtiva;
    private final List<Clube> catalogo = new ArrayList<>();
    private final Map<UUID, Long> valoresElencos = new HashMap<>();
    private final ObjectMapper json = new ObjectMapper();

    private void telaSplash() {
        VBox box = new VBox(12, label("GARFOOT", "brand"), label("Preparando seu próximo campeonato…", "subtle"));
        box.setAlignment(javafx.geometry.Pos.CENTER);
        box.setPadding(new Insets(50));
        mostrar(box, 620, 360);
        javafx.concurrent.Task<Void> tarefa = new javafx.concurrent.Task<>() {
            @Override protected Void call() { repositorio.listarIds(); return null; }
        };
        tarefa.setOnSucceeded(e -> telaMenu());
        tarefa.setOnFailed(e -> telaMenu());
        Thread thread = new Thread(tarefa, "garfoot-startup"); thread.setDaemon(true); thread.start();
    }

    private void telaMenu() {
        boolean haSave = !repositorio.listarIds().isEmpty();
        VBox menu = new VBox(12);
        menu.setPadding(new Insets(38)); menu.setAlignment(javafx.geometry.Pos.CENTER);
        menu.getChildren().addAll(label("GARFOOT", "brand"), label("Sua história no futebol começa aqui", "subtle"));
        Button novo = new Button("Novo Jogo"); novo.setOnAction(e -> perguntarCadastro());
        Button carregar = new Button("Carregar Jogo"); carregar.setDisable(!haSave); carregar.setOnAction(e -> carregarMaisRecente());
        Button conta = new Button("Conta · Free"); conta.setOnAction(e -> alerta("Conta Free", "O modo local está disponível. O serviço de contas ainda não foi configurado."));
        Button configuracoes = new Button("Configurações"); configuracoes.setOnAction(e -> alerta("Configurações", "Configurações iniciais serão salvas localmente nas próximas versões."));
        Button sair = new Button("Sair"); sair.setOnAction(e -> stage.close());
        for (Button b : List.of(novo, carregar, conta, configuracoes, sair)) { b.setMaxWidth(280); menu.getChildren().add(b); }
        mostrar(menu, 720, 560);
    }

    private void perguntarCadastro() {
        Alert dialogo = new Alert(Alert.AlertType.CONFIRMATION);
        dialogo.setTitle("Começar carreira"); dialogo.setHeaderText("Como deseja jogar?");
        dialogo.setContentText("Criar uma conta é opcional. Você pode começar agora no modo Free.");
        ButtonType free = new ButtonType("Jogar sem cadastro (Free)", ButtonBar.ButtonData.OK_DONE);
        ButtonType cadastro = new ButtonType("Criar conta agora", ButtonBar.ButtonData.OTHER);
        dialogo.getButtonTypes().setAll(free, cadastro, ButtonType.CANCEL);
        dialogo.showAndWait().ifPresent(escolha -> {
            if (escolha == free) telaNovoJogo();
            else if (escolha == cadastro) { alerta("Conta", "O cadastro ainda não está conectado a um serviço. Você pode continuar sem conta."); telaNovoJogo(); }
        });
    }

    private void telaNovoJogo() {
        try { carregarCatalogo(); } catch (Exception ex) { alerta("Catálogo", "Não foi possível abrir o catálogo local: " + ex.getMessage()); return; }
        ListView<Clube> clubes = new ListView<>();
        clubes.getItems().setAll(catalogo);
        clubes.setCellFactory(view -> new ListCell<>() {
            @Override protected void updateItem(Clube clube, boolean vazio) {
                super.updateItem(clube, vazio);
                setText(vazio || clube == null ? null : clube.nome() + "   ·   força " + Math.round(media(clube))
                        + "   ·   elenco " + formatarValor(clube));
            }
        });
        ComboBox<String> temporada = new ComboBox<>(); temporada.getItems().addAll("2026/27", "2027"); temporada.setValue("2026/27");
        ComboBox<String> dificuldade = new ComboBox<>(); dificuldade.getItems().addAll("Fácil", "Normal", "Difícil"); dificuldade.setValue("Normal");
        TextField tecnico = new TextField(); tecnico.setPromptText("Nome do técnico"); tecnico.setText("Novo Técnico");
        Button comecar = new Button("Revisar e começar");
        comecar.setOnAction(e -> {
            Clube clube = clubes.getSelectionModel().getSelectedItem();
            if (clube == null) { alerta("Escolha um clube", "Selecione um clube para continuar."); return; }
            if (tecnico.getText().isBlank()) { alerta("Nome do técnico", "Informe o nome do técnico."); return; }
            confirmarNovoSave(clube, tecnico.getText().trim(), temporada.getValue(), dificuldade.getValue());
        });
        VBox raiz = new VBox(12, label("Nova carreira", "section-title"), label("Escolha seu clube · Série A do Brasil", "subtle"),
                clubes, new Label("Elenco médio e valor de mercado são estimativas baseadas no snapshot local."),
                new Label("Técnico"), tecnico, new Label("Temporada inicial"), temporada,
                new Label("Dificuldade"), dificuldade, comecar);
        raiz.setPadding(new Insets(22));
        VBox.setVgrow(clubes, Priority.ALWAYS);
        mostrar(raiz, 760, 800);
    }

    private void confirmarNovoSave(Clube clube, String nomeTecnico, String ano, String dificuldade) {
        Alert dialogo = new Alert(Alert.AlertType.CONFIRMATION,
                "Clube: " + clube.nome() + "\nTécnico: " + nomeTecnico + "\nTemporada: " + ano
                        + "\nDificuldade: " + dificuldade + "\n\nCriar save e começar?", ButtonType.CANCEL, ButtonType.OK);
        dialogo.setTitle("Confirmar carreira"); dialogo.setHeaderText("Tudo pronto para começar");
        dialogo.showAndWait().filter(b -> b == ButtonType.OK).ifPresent(b -> criarSave(clube, nomeTecnico, ano, dificuldade));
    }

    private void criarSave(Clube escolhido, String nomeTecnico, String ano, String dificuldade) {
        Clube clube = copiarClube(escolhido);
        clube.definirTecnico(new Tecnico(UUID.randomUUID(), nomeTecnico));
        var formacao = Formacao.quatroQuatroDois();
        Map<Posicao, java.util.ArrayDeque<Jogador>> porPosicao = new EnumMap<>(Posicao.class);
        for (Posicao p : Posicao.values()) porPosicao.put(p, new java.util.ArrayDeque<>());
        clube.elenco().forEach(j -> porPosicao.get(j.posicao()).add(j));
        List<Jogador> titulares = new ArrayList<>();
        for (Posicao p : formacao.posicoesTitulares()) {
            if (porPosicao.get(p).isEmpty()) { alerta("Elenco incompleto", "Não há jogadores suficientes para montar a formação 4-4-2."); return; }
            titulares.add(porPosicao.get(p).removeFirst());
        }
        List<Jogador> reservas = porPosicao.values().stream().flatMap(Collection::stream).limit(7).toList();
        clube.definirTatica(new Tatica(new Escalacao(formacao, titulares, reservas), EstiloJogo.EQUILIBRADO));
        Campeonato campeonato = new Campeonato(UUID.randomUUID(), "Série A " + ano, TipoCompeticao.LIGA);
        catalogo.stream().map(this::copiarClube).forEach(campeonato::adicionarParticipante);
        campeonato.participantes().stream().filter(c -> c.id().equals(clube.id())).findFirst().ifPresent(c -> {
            c.definirTecnico(clube.tecnico()); c.definirTatica(clube.tatica());
        });
        new MotorCampeonato().gerarTurnoEReturno(campeonato, LocalDateTime.now().plusDays(1));
        new AtualizarClassificacao().executar(campeonato);
        repositorio.salvar(campeonato); temporadaAtiva = campeonato; abrirHub(campeonato, clubeId(campeonato, clube.id()));
    }

    private void carregarMaisRecente() {
        UUID id = repositorio.listarIds().stream().findFirst().orElse(null);
        if (id == null) { telaMenu(); return; }
        Campeonato c = repositorio.carregar(id).orElse(null);
        if (c == null) { alerta("Save", "Não foi possível carregar o save."); return; }
        temporadaAtiva = c;
        Clube controlado = c.participantes().stream().filter(cl -> cl.tecnico() != null).findFirst().orElse(c.participantes().getFirst());
        abrirHub(c, controlado);
    }

    private void abrirHub(Campeonato temporada, Clube clube) {
        try {
            AvancarRodada avancar = new AvancarRodada(new SimularPartida(new MotorSimulacaoPartida()), MainApp::forca);
            VisaoClubePresenter presenter = new VisaoClubePresenter(temporada, clube, avancar,
                    new AtualizarClassificacao(), new SalvarTemporada(repositorio));
            FXMLLoader loader = new FXMLLoader(getClass().getResource("/fxml/VisaoClube.fxml"));
            loader.setControllerFactory(tipo -> new VisaoClubeController(presenter));
            stage.setScene(new Scene(loader.load()));
        } catch (Exception ex) { alerta("Clube", "Falha ao abrir o clube: " + ex.getMessage()); telaMenu(); }
    }

    private void carregarCatalogo() throws Exception {
        if (!catalogo.isEmpty()) return;
        JsonNode fonte;
        Path processedClubs = Path.of("data/processed/transfermarkt/clubs.json");
        Path processedPlayers = Path.of("data/processed/transfermarkt/players.json");
        if (Files.exists(processedClubs) && Files.exists(processedPlayers)) {
            JsonNode clubesJson = json.readTree(processedClubs.toFile());
            JsonNode jogadoresJson = json.readTree(processedPlayers.toFile());
            Map<String, JsonNode> porId = new HashMap<>();
            clubesJson.forEach(c -> { if ("BRA1".equals(c.path("competition_id").asText())) porId.put(c.path("source_id").asText(), c); });
            Map<String, List<JsonNode>> atletas = new HashMap<>();
            jogadoresJson.forEach(j -> { String id=j.path("current_club_id").asText(); if (porId.containsKey(id)) atletas.computeIfAbsent(id, k -> new ArrayList<>()).add(j); });
            var lista = json.createArrayNode();
            porId.forEach((id, c) -> { com.fasterxml.jackson.databind.node.ObjectNode clone=c.deepCopy(); clone.set("players", json.valueToTree(atletas.getOrDefault(id,List.of()))); lista.add(clone); });
            fonte=lista;
        } else {
            try (InputStream stream=getClass().getResourceAsStream("/data/catalogo-bra1.json")) {
                if (stream == null) throw new IllegalStateException("catálogo inicial não encontrado");
                fonte=json.readTree(stream);
            }
        }
        GeradorRatingJogador ratings = new GeradorRatingJogador();
        for (JsonNode entry : fonte) {
            String clubeFonteId=entry.path("source_id").asText();
            List<JsonNode> atletas = new ArrayList<>(); entry.path("players").forEach(atletas::add);
            if (atletas.size() < 11) continue;
            String nome = entry.path("name").asText();
            UUID id = UUID.nameUUIDFromBytes(("tm-club-" + clubeFonteId).getBytes(StandardCharsets.UTF_8));
            Clube clube = new Clube(id, nome, nome.length() > 3 ? nome.substring(0, 3).toUpperCase(Locale.ROOT) : nome.toUpperCase(Locale.ROOT));
            int n=0;
            for (JsonNode a : atletas) {
                Posicao pos = posicao(a.path("position").asText()); if (pos == null) continue;
                LocalDate nasc;
                try { nasc=LocalDate.parse(a.path("date_of_birth").asText().substring(0,10)); } catch(Exception ex) { nasc=LocalDate.of(2000,1,1); }
                int idade = Math.max(15, Math.min(60, Period.between(nasc, LocalDate.now()).getYears()));
                int altura = a.path("height_in_cm").asInt(180);
                long valor; try { valor=Long.parseLong(a.path("market_value_in_eur").asText("0")); } catch(Exception ex) { valor=0; }
                var nota=ratings.gerar(new DadosRatingJogador(idade, Math.max(140,Math.min(230,altura)), Math.max(0,valor),0,0,0,0,0,pos));
                var attrs=new AtributosJogador(nota.tecnica(),nota.fisico(),nota.mental(),nota.velocidade(),nota.finalizacao(),nota.passe(),nota.marcacao(),nota.potencial());
                clube.adicionarJogador(new Jogador(UUID.nameUUIDFromBytes(("tm-player-"+a.path("source_id").asText()).getBytes(StandardCharsets.UTF_8)),a.path("name").asText("Jogador"),nasc,pos,attrs));
                valoresElencos.merge(id, Math.max(0, valor), Long::sum); n++;
            }
            clube.definirValorElencoEur(valoresElencos.getOrDefault(id,0L));
            if (n>=11) catalogo.add(clube);
        }
        catalogo.sort(Comparator.comparing(Clube::nome));
    }

    private Clube copiarClube(Clube origem) {
        Clube copia = new Clube(origem.id(), origem.nome(), origem.sigla());
        copia.definirValorElencoEur(origem.valorElencoEur());
        origem.elenco().forEach(j -> copia.adicionarJogador(new Jogador(j.id(), j.nome(), j.dataNascimento(), j.posicao(), j.atributos())));
        return copia;
    }
    private Clube clubeId(Campeonato c, UUID id) { return c.participantes().stream().filter(cl -> cl.id().equals(id)).findFirst().orElseThrow(); }
    private static Posicao posicao(String origem) {
        String s=origem.toLowerCase(Locale.ROOT);
        if(s.contains("goalkeeper"))return Posicao.GOL;
        if(s.contains("centre-back")||s.contains("defender"))return Posicao.ZAG;
        if(s.contains("right-back")||s.contains("left-back")||s.contains("wing-back"))return Posicao.LAT;
        if(s.contains("defensive midfield")||s.contains("midfield"))return s.contains("defensive")?Posicao.VOL:Posicao.MEI;
        if(s.contains("forward")||s.contains("winger")||s.contains("striker"))return Posicao.ATA;
        return null;
    }
    private static double media(Clube c) { return c.elenco().stream().mapToInt(j->(j.atributos().tecnica()+j.atributos().fisico()+j.atributos().mental())/3).average().orElse(0); }
    private String formatarValor(Clube c) { return "€"+String.format(Locale.ROOT,"%.1f mi", c.valorElencoEur()/1_000_000.0); }
    private void mostrar(javafx.scene.Node raiz, double largura, double altura) {
        Scene scene=new Scene((Parent)raiz,largura,altura); scene.getStylesheets().add(getClass().getResource("/css/visao-clube.css").toExternalForm()); stage.setScene(scene);
    }
    private Label label(String texto,String estilo) { Label l=new Label(texto); l.getStyleClass().add(estilo); return l; }
    private void alerta(String titulo,String texto) { Alert a=new Alert(Alert.AlertType.INFORMATION,texto,ButtonType.OK); a.setTitle(titulo); a.setHeaderText(null); a.showAndWait(); }

    private static Campeonato criarTemporadaDemo(UUID id) {
        Campeonato temporada = new Campeonato(id, "Liga de Demonstração", TipoCompeticao.LIGA);
        Clube clube = new Clube(UUID.randomUUID(), "Garfoot Atlético", "GAT");
        Clube adversario = new Clube(UUID.randomUUID(), "União Esportiva", "UNE");
        for (int index = 0; index < 11; index++) {
            Posicao posicao = Formacao.quatroQuatroDois().posicoesTitulares().get(index);
            clube.adicionarJogador(jogador("Atleta " + (index + 1), posicao, 66));
            adversario.adicionarJogador(jogador("Jogador " + (index + 1), posicao, 61));
        }
        temporada.adicionarParticipante(clube);
        temporada.adicionarParticipante(adversario);
        new MotorCampeonato().gerarTurnoEReturno(temporada, LocalDateTime.now().plusDays(1));
        return temporada;
    }

    private static Jogador jogador(String nome, Posicao posicao, int valor) {
        return new Jogador(UUID.randomUUID(), nome, LocalDate.of(2001, 1, 1), posicao,
                new AtributosJogador(valor, valor, valor, valor, valor, valor, valor, valor + 5));
    }

    private static ForcaEquipe forca(Clube clube) {
        return ForcaEquipe.aPartirDosJogadores(clube.elenco());
    }

    public static void main(String[] args) {
        launch(args);
    }
}
