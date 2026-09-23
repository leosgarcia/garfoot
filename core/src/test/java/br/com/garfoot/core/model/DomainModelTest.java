package br.com.garfoot.core.model;

import br.com.garfoot.core.model.campeonato.Campeonato;
import br.com.garfoot.core.model.campeonato.TipoCompeticao;
import br.com.garfoot.core.model.clube.Clube;
import br.com.garfoot.core.model.jogador.AtributosJogador;
import br.com.garfoot.core.model.jogador.Jogador;
import br.com.garfoot.core.model.jogador.Posicao;
import br.com.garfoot.core.model.jogador.StatusJogador;
import br.com.garfoot.core.model.partida.EventoPartida;
import br.com.garfoot.core.model.partida.Partida;
import br.com.garfoot.core.model.partida.TipoEvento;
import br.com.garfoot.core.model.tatica.Escalacao;
import br.com.garfoot.core.model.tatica.Formacao;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class DomainModelTest {
    @Test
    void rejectsPlayerAttributeOutsideDomainRange() {
        assertThrows(IllegalArgumentException.class, () -> new AtributosJogador(101, 50, 50, 50, 50, 50, 50, 50));
    }

    @Test
    void protectsClubRosterAndRejectsDuplicatePlayer() {
        Clube clube = new Clube(UUID.randomUUID(), "Garfoot FC", "GFC");
        Jogador jogador = jogador("Jogador 1");

        clube.adicionarJogador(jogador);

        assertEquals(1, clube.elenco().size());
        assertThrows(UnsupportedOperationException.class, () -> clube.elenco().clear());
        assertThrows(IllegalArgumentException.class, () -> clube.adicionarJogador(jogador));
    }

    @Test
    void matchStartsRecordsEventAndFinishes() {
        Partida partida = new Partida(
                UUID.randomUUID(),
                new Clube(UUID.randomUUID(), "Mandante", "MAN"),
                new Clube(UUID.randomUUID(), "Visitante", "VIS"),
                LocalDateTime.now());

        partida.iniciar();
        partida.registrarGolMandante();
        partida.registrarEvento(new EventoPartida(42, TipoEvento.GOL, null, "Gol do mandante"));
        partida.encerrar();

        assertEquals(1, partida.golsMandante());
        assertEquals(1, partida.eventos().size());
    }

    @Test
    void rejectsMatchWithSameClubOnBothSides() {
        Clube clube = new Clube(UUID.randomUUID(), "Mesmo Clube", "MSC");

        assertThrows(IllegalArgumentException.class, () -> new Partida(
                UUID.randomUUID(), clube, clube, LocalDateTime.now()));
    }

    @Test
    void championshipRejectsDuplicateParticipant() {
        Campeonato campeonato = new Campeonato(UUID.randomUUID(), "Liga Garfoot", TipoCompeticao.LIGA);
        Clube clube = new Clube(UUID.randomUUID(), "Garfoot FC", "GFC");

        campeonato.adicionarParticipante(clube);

        assertThrows(IllegalArgumentException.class, () -> campeonato.adicionarParticipante(clube));
    }

    @Test
    void lineupAcceptsMatchingAvailablePlayersAndRejectsDuplicateOrUnavailablePlayers() {
        Formacao formacao = Formacao.quatroQuatroDois();
        List<Jogador> titulares = formacao.posicoesTitulares().stream()
                .map(posicao -> jogador("Titular " + posicao + UUID.randomUUID(), posicao))
                .toList();
        Jogador reserva = jogador("Reserva", Posicao.MEI);

        Escalacao escalacao = new Escalacao(formacao, titulares, List.of(reserva));
        assertEquals(11, escalacao.titulares().size());
        assertThrows(IllegalArgumentException.class, () -> new Escalacao(formacao,
                titulares.subList(0, 10), List.of(reserva)));
        assertThrows(IllegalArgumentException.class, () -> new Escalacao(formacao,
                titulares, List.of(titulares.get(0))));

        reserva.atualizarStatus(StatusJogador.LESIONADO);
        assertThrows(IllegalArgumentException.class, () -> new Escalacao(formacao, titulares, List.of(reserva)));
    }

    private static Jogador jogador(String nome) {
        return jogador(nome, Posicao.MEI);
    }

    private static Jogador jogador(String nome, Posicao posicao) {
        return new Jogador(
                UUID.randomUUID(),
                nome,
                LocalDate.of(2000, 1, 1),
                posicao,
                new AtributosJogador(50, 50, 50, 50, 50, 50, 50, 60));
    }
}
