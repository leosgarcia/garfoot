package br.com.garfoot.core.engine;

import br.com.garfoot.core.model.campeonato.Campeonato;
import br.com.garfoot.core.model.campeonato.Rodada;
import br.com.garfoot.core.model.campeonato.TipoCompeticao;
import br.com.garfoot.core.model.clube.Clube;
import br.com.garfoot.core.model.jogador.AtributosJogador;
import br.com.garfoot.core.model.jogador.Jogador;
import br.com.garfoot.core.model.jogador.Posicao;
import br.com.garfoot.core.model.tatica.Escalacao;
import br.com.garfoot.core.model.tatica.Formacao;
import br.com.garfoot.core.model.partida.Partida;
import br.com.garfoot.core.model.partida.StatusPartida;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;
import java.time.LocalDate;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class MotorCampeonatoTest {
    private final MotorCampeonato motor = new MotorCampeonato();

    @Test
    void generatesEachFixtureOncePerLegAndReversesHomeSide() {
        Campeonato campeonato = campeonato(5);
        List<Rodada> rodadas = motor.gerarTurnoEReturno(campeonato, LocalDateTime.of(2026, 1, 1, 12, 0));

        assertEquals(10, rodadas.size());
        assertEquals(20, rodadas.stream().mapToInt(rodada -> rodada.partidas().size()).sum());
        Set<String> jogosPrimeiroTurno = new HashSet<>();
        Set<String> jogosSegundoTurno = new HashSet<>();
        for (Partida partida : rodadas.subList(0, 5).stream().flatMap(r -> r.partidas().stream()).toList()) {
            assertTrue(jogosPrimeiroTurno.add(chave(partida.mandante(), partida.visitante())));
        }
        for (Partida partida : rodadas.subList(5, 10).stream().flatMap(r -> r.partidas().stream()).toList()) {
            assertTrue(jogosSegundoTurno.add(chave(partida.mandante(), partida.visitante())));
        }
        assertEquals(10, jogosPrimeiroTurno.size());
        assertEquals(10, jogosSegundoTurno.size());
        for (String fixture : jogosPrimeiroTurno) {
            String[] clubs = fixture.split(":");
            assertTrue(jogosSegundoTurno.contains(clubs[1] + ":" + clubs[0]));
        }
    }

    @Test
    void seasonUsesSeedAndUpdatesAllStandingsAndMatchStates() {
        Campeonato primeira = campeonato(4);
        Campeonato segunda = campeonato(4);
        motor.gerarTurnoEReturno(primeira, LocalDateTime.of(2026, 1, 1, 12, 0));
        motor.gerarTurnoEReturno(segunda, LocalDateTime.of(2026, 1, 1, 12, 0));

        motor.simularTemporada(primeira, 907L);
        motor.simularTemporada(segunda, 907L);

        assertEquals(primeira.rodadas().stream().flatMap(r -> r.partidas().stream())
                        .map(p -> p.golsMandante() + ":" + p.golsVisitante()).toList(),
                segunda.rodadas().stream().flatMap(r -> r.partidas().stream())
                        .map(p -> p.golsMandante() + ":" + p.golsVisitante()).toList());
        assertEquals(4, primeira.classificacao().size());
        assertTrue(primeira.classificacao().stream().allMatch(item -> item.vitorias() + item.empates() + item.derrotas() == 6));
        assertTrue(primeira.classificacao().stream().allMatch(item -> item.pontos() == item.vitorias() * 3 + item.empates()));
        assertTrue(primeira.rodadas().stream().flatMap(r -> r.partidas().stream())
                .allMatch(partida -> partida.status() == StatusPartida.ENCERRADA));
    }

    @Test
    void hundredCompleteSeasonsKeepGoalsAndExtremesWithinExpectedBounds() {
        int matches = 0;
        int goals = 0;
        int nilNil = 0;
        int extreme = 0;
        for (long seasonSeed = 0; seasonSeed < 100; seasonSeed++) {
            Campeonato temporada = campeonato(4);
            motor.gerarTurnoEReturno(temporada, LocalDateTime.of(2026, 1, 1, 12, 0));
            motor.simularTemporada(temporada, seasonSeed * 101);
            for (Partida partida : temporada.rodadas().stream().flatMap(rodada -> rodada.partidas().stream()).toList()) {
                matches++;
                goals += partida.golsMandante() + partida.golsVisitante();
                if (partida.golsMandante() == 0 && partida.golsVisitante() == 0) nilNil++;
                if (Math.max(partida.golsMandante(), partida.golsVisitante()) >= 8) extreme++;
            }
        }
        double mediaGols = goals / (double) matches;
        double taxaZeroZero = nilNil / (double) matches;
        System.out.printf("SEASONS count=100 matches=%d avgGoals=%.3f nilNil=%.3f extreme8=%d%n",
                matches, mediaGols, taxaZeroZero, extreme);
        assertEquals(1_200, matches);
        assertTrue(mediaGols > 1.5 && mediaGols < 2.5);
        assertTrue(taxaZeroZero > 0.05 && taxaZeroZero < 0.30);
        assertEquals(0, extreme);
    }

    @Test
    void fiftyCompleteSeasonsWithPositionalSquadsCompareCompetitiveLevelsAndScorers() {
        int matches = 0;
        int goals = 0;
        int nilNil = 0;
        int extreme = 0;
        java.util.Map<Integer, Integer> pointsByLevel = new java.util.TreeMap<>();
        java.util.Map<Posicao, Long> goalsByPosition = new java.util.EnumMap<>(Posicao.class);
        for (long seed = 0; seed < 50; seed++) {
            Campeonato temporada = temporadaPosicional();
            motor.gerarTurnoEReturno(temporada, LocalDateTime.of(2026, 1, 1, 12, 0));
            motor.simularTemporada(temporada, seed * 137);
            for (var item : temporada.classificacao()) {
                int level = Integer.parseInt(item.clube().sigla());
                pointsByLevel.merge(level, item.pontos(), Integer::sum);
            }
            for (Partida partida : temporada.rodadas().stream().flatMap(rodada -> rodada.partidas().stream()).toList()) {
                matches++;
                goals += partida.golsMandante() + partida.golsVisitante();
                if (partida.golsMandante() == 0 && partida.golsVisitante() == 0) nilNil++;
                if (Math.max(partida.golsMandante(), partida.golsVisitante()) >= 8) extreme++;
                partida.eventos().stream().filter(evento -> evento.tipo()
                                == br.com.garfoot.core.model.partida.TipoEvento.GOL)
                        .flatMap(evento -> evento.jogador().stream())
                        .forEach(jogador -> goalsByPosition.merge(jogador.posicao(), 1L, Long::sum));
            }
        }
        long totalGoals = goalsByPosition.values().stream().mapToLong(Long::longValue).sum();
        double averageGoals = goals / (double) matches;
        double nilNilRate = nilNil / (double) matches;
        double strikerShare = goalsByPosition.getOrDefault(Posicao.ATA, 0L) / (double) totalGoals;
        double goalkeeperShare = goalsByPosition.getOrDefault(Posicao.GOL, 0L) / (double) totalGoals;
        System.out.printf("SEASONS positional count=50 matches=%d avgGoals=%.3f nilNil=%.3f pointsByLevel=%s goalsByPosition=%s%n",
                matches, averageGoals, nilNilRate, pointsByLevel, goalsByPosition);
        assertEquals(600, matches);
        assertTrue(averageGoals > 1.4 && averageGoals < 3.0);
        assertTrue(nilNilRate > 0.03 && nilNilRate < 0.35);
        assertEquals(0, extreme);
        assertTrue(pointsByLevel.get(85) > pointsByLevel.get(40));
        assertTrue(strikerShare > 0.30, "striker goal share: " + strikerShare);
        assertTrue(goalkeeperShare < 0.03, "goalkeeper goal share: " + goalkeeperShare);
    }

    private static Campeonato temporadaPosicional() {
        Campeonato temporada = new Campeonato(UUID.randomUUID(), "Liga Posicional", TipoCompeticao.LIGA);
        for (int level : new int[]{40, 55, 70, 85}) {
            Clube clube = new Clube(UUID.randomUUID(), "Clube " + level, Integer.toString(level));
            Formacao formacao = Formacao.quatroQuatroDois();
            List<Jogador> titulares = formacao.posicoesTitulares().stream()
                    .map(posicao -> jogadorPosicional(posicao, level)).toList();
            List<Jogador> reservas = List.of(Posicao.GOL, Posicao.ZAG, Posicao.LAT, Posicao.MEI, Posicao.ATA)
                    .stream().map(posicao -> jogadorPosicional(posicao, level - 2)).toList();
            Escalacao escalacao = new Escalacao(formacao, titulares, reservas);
            java.util.stream.Stream.concat(escalacao.titulares().stream(), escalacao.reservas().stream())
                    .forEach(clube::adicionarJogador);
            temporada.adicionarParticipante(clube);
        }
        return temporada;
    }

    private static Jogador jogadorPosicional(Posicao posicao, int nivel) {
        int[] base = switch (posicao) {
            case GOL -> new int[]{42, 62, 72, 40, 18, 45, 92};
            case ZAG -> new int[]{50, 70, 72, 55, 38, 52, 86};
            case LAT -> new int[]{55, 70, 64, 78, 38, 65, 72};
            case VOL -> new int[]{58, 70, 72, 58, 38, 70, 78};
            case MEI -> new int[]{78, 58, 64, 66, 60, 82, 48};
            case ATA -> new int[]{65, 70, 64, 78, 88, 56, 34};
        };
        int[] escalados = java.util.Arrays.stream(base)
                .map(valor -> Math.max(0, Math.min(100, (int) Math.round(valor * nivel / 60.0))))
                .toArray();
        return new Jogador(UUID.randomUUID(), "Atleta " + UUID.randomUUID(), LocalDate.of(2000, 1, 1),
                posicao, new AtributosJogador(escalados[0], escalados[1], escalados[2], escalados[3],
                escalados[4], escalados[5], escalados[6], Math.min(100, nivel + 5)));
    }

    private static Campeonato campeonato(int clubes) {
        Campeonato campeonato = new Campeonato(UUID.randomUUID(), "Liga", TipoCompeticao.LIGA);
        for (int index = 0; index < clubes; index++) {
            campeonato.adicionarParticipante(new Clube(UUID.randomUUID(), "Clube " + index, "C" + index));
        }
        return campeonato;
    }

    private static String chave(Clube mandante, Clube visitante) {
        return mandante.nome() + ":" + visitante.nome();
    }
}
