package br.com.garfoot.core.application.usecase;

import br.com.garfoot.core.engine.ForcaEquipe;
import br.com.garfoot.core.engine.MotorSimulacaoPartida;
import br.com.garfoot.core.model.campeonato.Campeonato;
import br.com.garfoot.core.model.campeonato.Rodada;
import br.com.garfoot.core.model.campeonato.TipoCompeticao;
import br.com.garfoot.core.model.clube.Clube;
import br.com.garfoot.core.model.partida.Partida;
import br.com.garfoot.core.model.partida.StatusPartida;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class ApplicationUseCaseTest {
    @Test
    void advanceRoundSimulatesMatchesAndRecalculateStandings() {
        Campeonato campeonato = new Campeonato(UUID.randomUUID(), "Liga", TipoCompeticao.LIGA);
        Clube casa = new Clube(UUID.randomUUID(), "Casa", "CAS");
        Clube fora = new Clube(UUID.randomUUID(), "Fora", "FOR");
        campeonato.adicionarParticipante(casa);
        campeonato.adicionarParticipante(fora);
        Rodada rodada = new Rodada(1);
        Partida partida = new Partida(UUID.randomUUID(), casa, fora, LocalDateTime.of(2026, 1, 1, 12, 0));
        rodada.adicionarPartida(partida);
        campeonato.adicionarRodada(rodada);

        SimularPartida simular = new SimularPartida(new MotorSimulacaoPartida());
        new AvancarRodada(simular, clube -> new ForcaEquipe(60, 60)).executar(rodada, 11L);
        new AtualizarClassificacao().executar(campeonato);

        assertEquals(StatusPartida.ENCERRADA, partida.status());
        assertEquals(2, campeonato.classificacao().size());
        assertEquals(campeonato.classificacao().stream().mapToInt(item -> item.vitorias() * 3 + item.empates()).sum(),
                campeonato.classificacao().stream().mapToInt(item -> item.pontos()).sum());
    }

    @Test
    void loadSeasonUsesRepositoryPortAndReportsMissingId() {
        UUID seasonId = UUID.randomUUID();
        Campeonato season = new Campeonato(seasonId, "Liga", TipoCompeticao.LIGA);
        CarregarTemporada useCase = new CarregarTemporada(new br.com.garfoot.core.application.port.RepositorioTemporada() {
            @Override public void salvar(Campeonato ignored) { }
            @Override public Optional<Campeonato> carregar(UUID id) {
                return id.equals(seasonId) ? Optional.of(season) : Optional.empty();
            }
        });

        assertEquals(season, useCase.executar(seasonId));
        assertThrows(IllegalArgumentException.class, () -> useCase.executar(UUID.randomUUID()));
    }
}
