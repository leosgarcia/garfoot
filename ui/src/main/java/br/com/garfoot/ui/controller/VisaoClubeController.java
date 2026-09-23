package br.com.garfoot.ui.controller;

import br.com.garfoot.ui.presentation.EstadoVisaoClube;
import br.com.garfoot.ui.presentation.VisaoClubePresenter;
import javafx.fxml.FXML;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.ListView;

import java.util.Objects;

public final class VisaoClubeController {
    private final VisaoClubePresenter presenter;

    @FXML private Label clubeNome;
    @FXML private Label proximaPartida;
    @FXML private Label ultimoResultado;
    @FXML private Label estadoLabel;
    @FXML private ListView<String> elencoLista;
    @FXML private ListView<String> classificacaoLista;
    @FXML private Button avancarButton;

    public VisaoClubeController(VisaoClubePresenter presenter) {
        this.presenter = Objects.requireNonNull(presenter);
    }

    @FXML
    private void initialize() {
        aplicar(new EstadoVisaoClube(EstadoVisaoClube.Status.CARREGANDO, "Garfoot",
                java.util.List.of(), "Carregando…", java.util.List.of(), "Carregando…", "Carregando…", false));
        aplicar(presenter.carregar());
    }

    @FXML
    private void avancarRodada() {
        estadoLabel.setText("Simulando rodada…");
        avancarButton.setDisable(true);
        aplicar(presenter.avancar());
    }

    private void aplicar(EstadoVisaoClube estado) {
        clubeNome.setText(estado.nomeClube());
        proximaPartida.setText(estado.proximaPartida());
        ultimoResultado.setText(estado.ultimoResultado());
        estadoLabel.setText(estado.mensagem());
        elencoLista.getItems().setAll(estado.elenco());
        classificacaoLista.getItems().setAll(estado.classificacao());
        avancarButton.setDisable(!estado.podeAvancar());
        estadoLabel.getStyleClass().removeAll("status-error");
        if (estado.status() == EstadoVisaoClube.Status.ERRO) {
            estadoLabel.getStyleClass().add("status-error");
        }
    }
}
