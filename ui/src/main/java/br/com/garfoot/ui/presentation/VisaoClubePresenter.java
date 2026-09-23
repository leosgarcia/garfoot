package br.com.garfoot.ui.presentation;

import br.com.garfoot.core.application.usecase.AtualizarClassificacao;
import br.com.garfoot.core.application.usecase.AvancarRodada;
import br.com.garfoot.core.application.usecase.SalvarTemporada;
import br.com.garfoot.core.model.campeonato.Campeonato;
import br.com.garfoot.core.model.campeonato.ClassificacaoItem;
import br.com.garfoot.core.model.clube.Clube;
import br.com.garfoot.core.model.partida.Partida;
import br.com.garfoot.core.model.partida.StatusPartida;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public final class VisaoClubePresenter {
    private final Campeonato temporada;
    private final Clube clube;
    private final AvancarRodada avancarRodada;
    private final AtualizarClassificacao atualizarClassificacao;
    private final SalvarTemporada salvarTemporada;
    private long seed = 1;

    public VisaoClubePresenter(Campeonato temporada, Clube clube, AvancarRodada avancarRodada,
                               AtualizarClassificacao atualizarClassificacao, SalvarTemporada salvarTemporada) {
        this.temporada = Objects.requireNonNull(temporada);
        this.clube = Objects.requireNonNull(clube);
        this.avancarRodada = Objects.requireNonNull(avancarRodada);
        this.atualizarClassificacao = Objects.requireNonNull(atualizarClassificacao);
        this.salvarTemporada = Objects.requireNonNull(salvarTemporada);
    }

    public EstadoVisaoClube carregar() {
        try {
            return montarEstado();
        } catch (RuntimeException exception) {
            return erro("Não foi possível carregar a visão do clube: " + mensagem(exception));
        }
    }

    public EstadoVisaoClube avancar() {
        try {
            var rodada = temporada.rodadas().stream()
                    .filter(item -> item.partidas().stream().anyMatch(p -> p.status() == StatusPartida.AGENDADA))
                    .findFirst().orElseThrow(() -> new IllegalStateException("Não há rodadas pendentes."));
            avancarRodada.executar(rodada, seed++);
            atualizarClassificacao.executar(temporada);
            salvarTemporada.executar(temporada);
            EstadoVisaoClube estado = montarEstado();
            return new EstadoVisaoClube(estado.status(), estado.nomeClube(), estado.elenco(),
                    estado.proximaPartida(), estado.classificacao(), estado.ultimoResultado(),
                    "Rodada " + rodada.numero() + " simulada e salva.", estado.podeAvancar());
        } catch (RuntimeException exception) {
            return erro("Não foi possível avançar: " + mensagem(exception));
        }
    }

    private EstadoVisaoClube montarEstado() {
        if (temporada.participantes().stream().noneMatch(item -> item.id().equals(clube.id()))) {
            return new EstadoVisaoClube(EstadoVisaoClube.Status.VAZIO, clube.nome(), List.of(),
                    "Nenhuma temporada disponível", List.of(), "Ainda não há resultado",
                    "O clube não participa desta temporada.", false);
        }
        List<String> elenco = clube.elenco().stream()
                .map(jogador -> jogador.nome() + " · " + jogador.posicao()).toList();
        Partida proxima = partidas().stream().filter(partida -> partida.status() == StatusPartida.AGENDADA)
                .filter(this::envolveClube).findFirst().orElse(null);
        String proximaTexto = proxima == null ? "Nenhuma partida agendada"
                : proxima.mandante().nome() + " × " + proxima.visitante().nome();
        List<Partida> partidasRecentes = partidas();
        Collections.reverse(partidasRecentes);
        Partida ultima = partidasRecentes.stream().filter(partida -> partida.status() == StatusPartida.ENCERRADA)
                .filter(this::envolveClube).findFirst().orElse(null);
        String resultado = ultima == null ? "Ainda não há resultado"
                : ultima.mandante().nome() + " " + ultima.golsMandante() + " × " + ultima.golsVisitante()
                + " " + ultima.visitante().nome();
        List<ClassificacaoItem> itens = temporada.classificacao();
        List<String> classificacao = java.util.stream.IntStream.range(0, itens.size())
                .mapToObj(index -> (index + 1) + ". " + itens.get(index).clube().nome()
                        + " · " + itens.get(index).pontos() + " pts").toList();
        boolean vazio = elenco.isEmpty() && partidas().isEmpty() && itens.isEmpty();
        return new EstadoVisaoClube(vazio ? EstadoVisaoClube.Status.VAZIO : EstadoVisaoClube.Status.PRONTO,
                clube.nome(), elenco.isEmpty() ? List.of("Elenco vazio") : elenco,
                proximaTexto, classificacao.isEmpty() ? List.of("Classificação indisponível") : classificacao,
                resultado, vazio ? "Não há dados para exibir." : "Pronto",
                temporada.rodadas().stream().flatMap(rodada -> rodada.partidas().stream())
                        .anyMatch(partida -> partida.status() == StatusPartida.AGENDADA));
    }

    private List<Partida> partidas() {
        return new ArrayList<>(temporada.rodadas().stream().flatMap(rodada -> rodada.partidas().stream()).toList());
    }

    private boolean envolveClube(Partida partida) {
        return partida.mandante().id().equals(clube.id()) || partida.visitante().id().equals(clube.id());
    }

    private EstadoVisaoClube erro(String mensagem) {
        return new EstadoVisaoClube(EstadoVisaoClube.Status.ERRO, clube.nome(), List.of(),
                "Indisponível", List.of(), "Indisponível", mensagem, false);
    }

    private static String mensagem(RuntimeException exception) {
        return exception.getMessage() == null ? exception.getClass().getSimpleName() : exception.getMessage();
    }
}
