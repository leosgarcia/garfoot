package br.com.garfoot.ui.presentation;

import br.com.garfoot.core.application.port.RepositorioTemporada;
import br.com.garfoot.core.application.usecase.AtualizarClassificacao;
import br.com.garfoot.core.application.usecase.AvancarRodada;
import br.com.garfoot.core.application.usecase.SalvarTemporada;
import br.com.garfoot.core.application.usecase.SimularPartida;
import br.com.garfoot.core.engine.ForcaEquipe;
import br.com.garfoot.core.engine.MotorSimulacaoPartida;
import br.com.garfoot.core.model.campeonato.Campeonato;
import br.com.garfoot.core.model.campeonato.Rodada;
import br.com.garfoot.core.model.campeonato.TipoCompeticao;
import br.com.garfoot.core.model.clube.Clube;
import br.com.garfoot.core.model.partida.Partida;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class VisaoClubePresenterTest {
    @Test
    void presentsEmptySeasonStateWithoutEnablingAdvance() {
        Campeonato temporada = new Campeonato(UUID.randomUUID(), "Liga", TipoCompeticao.LIGA);
        Clube clube = clube("Clube");
        temporada.adicionarParticipante(clube);

        EstadoVisaoClube estado = presenter(temporada, clube, id -> { }).carregar();

        assertEquals(EstadoVisaoClube.Status.VAZIO, estado.status());
        assertFalse(estado.podeAvancar());
        assertTrue(estado.mensagem().contains("Não há dados"));
    }

    @Test
    void advancesMatchUpdatesViewAndSavesSeason() {
        Campeonato temporada = temporadaComPartida();
        Clube clube = temporada.participantes().getFirst();
        AtomicInteger saves = new AtomicInteger();
        VisaoClubePresenter presenter = presenter(temporada, clube, id -> saves.incrementAndGet());

        EstadoVisaoClube antes = presenter.carregar();
        EstadoVisaoClube depois = presenter.avancar();

        assertEquals(EstadoVisaoClube.Status.PRONTO, antes.status());
        assertTrue(antes.podeAvancar());
        assertEquals(EstadoVisaoClube.Status.PRONTO, depois.status());
        assertEquals(1, saves.get());
        assertFalse(depois.podeAvancar());
        assertTrue(depois.ultimoResultado().contains("×"));
        assertTrue(depois.mensagem().contains("simulada e salva"));
    }

    @Test
    void exposesSaveFailureAsAnErrorState() {
        Campeonato temporada = temporadaComPartida();
        Clube clube = temporada.participantes().getFirst();
        VisaoClubePresenter presenter = presenter(temporada, clube, id -> {
            throw new IllegalStateException("disco indisponível");
        });

        EstadoVisaoClube estado = presenter.avancar();

        assertEquals(EstadoVisaoClube.Status.ERRO, estado.status());
        assertTrue(estado.mensagem().contains("disco indisponível"));
        assertFalse(estado.podeAvancar());
    }

    private static VisaoClubePresenter presenter(Campeonato temporada, Clube clube,
                                                  java.util.function.Consumer<Campeonato> salvar) {
        SimularPartida simular = new SimularPartida(new MotorSimulacaoPartida());
        AvancarRodada avancar = new AvancarRodada(simular, item -> new ForcaEquipe(60, 60));
        SalvarTemporada salvarTemporada = new SalvarTemporada(new RepositorioTemporada() {
            @Override public void salvar(Campeonato campeonato) { salvar.accept(campeonato); }
            @Override public Optional<Campeonato> carregar(UUID id) { return Optional.empty(); }
        });
        return new VisaoClubePresenter(temporada, clube, avancar, new AtualizarClassificacao(), salvarTemporada);
    }

    private static Campeonato temporadaComPartida() {
        Campeonato temporada = new Campeonato(UUID.randomUUID(), "Liga", TipoCompeticao.LIGA);
        Clube mandante = clube("Mandante");
        Clube visitante = clube("Visitante");
        temporada.adicionarParticipante(mandante);
        temporada.adicionarParticipante(visitante);
        Rodada rodada = new Rodada(1);
        rodada.adicionarPartida(new Partida(UUID.randomUUID(), mandante, visitante,
                LocalDateTime.of(2026, 1, 1, 12, 0)));
        temporada.adicionarRodada(rodada);
        return temporada;
    }

    private static Clube clube(String nome) {
        return new Clube(UUID.randomUUID(), nome, nome.substring(0, 3).toUpperCase());
    }
}
