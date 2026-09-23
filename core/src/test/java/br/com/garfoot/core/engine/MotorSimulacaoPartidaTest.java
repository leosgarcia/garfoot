package br.com.garfoot.core.engine;

import br.com.garfoot.core.model.jogador.RatingJogador;
import br.com.garfoot.core.model.jogador.AtributosJogador;
import br.com.garfoot.core.model.jogador.Jogador;
import br.com.garfoot.core.model.jogador.Posicao;
import br.com.garfoot.core.model.clube.Clube;
import br.com.garfoot.core.model.tatica.Escalacao;
import br.com.garfoot.core.model.tatica.Formacao;
import br.com.garfoot.core.model.partida.Partida;
import br.com.garfoot.core.model.partida.StatusPartida;
import br.com.garfoot.core.model.partida.TipoEvento;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class MotorSimulacaoPartidaTest {
    private final MotorSimulacaoPartida motor = new MotorSimulacaoPartida();
    private final ForcaEquipe equipeForte = ForcaEquipe.aPartirDe(List.of(rating(78)));
    private final ForcaEquipe equipeMedia = ForcaEquipe.aPartirDe(List.of(rating(60)));

    @Test
    void fixedSeedProducesTheSameResult() {
        ResultadoSimulacao primeiro = motor.simular(equipeForte, equipeMedia, 42L);
        ResultadoSimulacao segundo = motor.simular(equipeForte, equipeMedia, 42L);

        assertEquals(primeiro, segundo);
    }

    @Test
    void differentSeedsCanProduceDifferentResults() {
        long placaresDiferentes = java.util.stream.LongStream.range(1, 20)
                .mapToObj(seed -> motor.simular(equipeMedia, equipeMedia, seed))
                .map(resultado -> resultado.golsMandante() + ":" + resultado.golsVisitante())
                .distinct()
                .count();

        assertTrue(placaresDiferentes > 1);
    }

    @Test
    void distributionHasPlausibleGoalsAndOrderedEvents() {
        int totalGols = 0;
        int maiorPlacar = 0;
        int partidasSemGols = 0;

        for (long seed = 0; seed < 1_000; seed++) {
            ResultadoSimulacao resultado = motor.simular(equipeMedia, equipeMedia, seed);
            totalGols += resultado.golsMandante() + resultado.golsVisitante();
            maiorPlacar = Math.max(maiorPlacar, Math.max(resultado.golsMandante(), resultado.golsVisitante()));
            if (resultado.golsMandante() == 0 && resultado.golsVisitante() == 0) {
                partidasSemGols++;
            }
            for (int index = 1; index < resultado.eventos().size(); index++) {
                assertTrue(resultado.eventos().get(index - 1).minuto() <= resultado.eventos().get(index).minuto());
            }
        }

        double mediaGols = totalGols / 1_000.0;
        assertTrue(mediaGols > 1.0 && mediaGols < 3.5, "media de gols: " + mediaGols);
        assertTrue(maiorPlacar <= 10, "maior placar: " + maiorPlacar);
        assertTrue(partidasSemGols > 0 && partidasSemGols < 500, "0-0: " + partidasSemGols);
    }

    @Test
    void competitiveLevelsShowIncreasingWinRateWithoutExtremeScoreConcentration() {
        int[] levels = {35, 50, 65, 85};
        double[] winRates = new double[levels.length];
        for (int levelIndex = 0; levelIndex < levels.length; levelIndex++) {
            ForcaEquipe forte = new ForcaEquipe(levels[levelIndex], levels[levelIndex]);
            ForcaEquipe fraca = new ForcaEquipe(100 - levels[levelIndex], 100 - levels[levelIndex]);
            int wins = 0;
            int extreme = 0;
            for (long seed = 0; seed < 2_000; seed++) {
                ResultadoSimulacao resultado = motor.simular(forte, fraca, seed);
                if (resultado.golsMandante() > resultado.golsVisitante()) wins++;
                if (Math.max(resultado.golsMandante(), resultado.golsVisitante()) >= 8) extreme++;
            }
            winRates[levelIndex] = wins / 2_000.0;
            assertTrue(extreme < 20, "extreme scores at level " + levels[levelIndex] + ": " + extreme);
        }
        assertTrue(winRates[0] < winRates[1] && winRates[1] < winRates[2] && winRates[2] < winRates[3],
                "stronger teams should win more often: " + java.util.Arrays.toString(winRates));
        System.out.println("BALANCE strong-team-win-rates=" + java.util.Arrays.toString(winRates));
    }

    @Test
    void reportsNeutralMatchBalanceMetrics() {
        int totalGoals = 0;
        int draws = 0;
        int homeWins = 0;
        int nilNil = 0;
        int extreme = 0;
        int sample = 10_000;
        for (long seed = 0; seed < sample; seed++) {
            ResultadoSimulacao resultado = motor.simular(equipeMedia, equipeMedia, seed);
            totalGoals += resultado.golsMandante() + resultado.golsVisitante();
            if (resultado.golsMandante() == resultado.golsVisitante()) draws++;
            if (resultado.golsMandante() > resultado.golsVisitante()) homeWins++;
            if (resultado.golsMandante() == 0 && resultado.golsVisitante() == 0) nilNil++;
            if (Math.max(resultado.golsMandante(), resultado.golsVisitante()) >= 8) extreme++;
        }
        System.out.printf("BALANCE sample=%d avgGoals=%.3f homeWin=%.3f draw=%.3f nilNil=%.3f extreme8=%d%n",
                sample, totalGoals / (double) sample, homeWins / (double) sample,
                draws / (double) sample, nilNil / (double) sample, extreme);
        assertTrue(totalGoals > 0);
    }

    @Test
    void positionalFourFourTwoSquadsPreserveStrengthCorrelationAndPlayerEvents() {
        int[] levels = {35, 50, 65, 85};
        double[] winRates = new double[levels.length];
        Squad[] squads = java.util.Arrays.stream(levels).mapToObj(MotorSimulacaoPartidaTest::squad).toArray(Squad[]::new);
        for (int levelIndex = 0; levelIndex < levels.length; levelIndex++) {
            int wins = 0;
            Squad forte = squads[levelIndex];
            Squad adversario = squads[levels.length - 1 - levelIndex];
            for (long seed = 0; seed < 1_000; seed++) {
                ResultadoSimulacao resultado = motor.simular(forte.forca(), adversario.forca(),
                        forte.elenco(), adversario.elenco(), seed);
                if (resultado.golsMandante() > resultado.golsVisitante()) wins++;
                assertTrue(resultado.eventos().stream().allMatch(evento -> {
                    var envolvidos = java.util.stream.Stream.of(evento.jogadorEnvolvido(),
                                    evento.jogadorQueSai(), evento.jogadorQueEntra())
                            .filter(java.util.Objects::nonNull).map(Jogador::id).toList();
                    if (evento.descricaoNarrativa().contains("mandante")) {
                        return envolvidos.stream().allMatch(forte.ids()::contains);
                    }
                    if (evento.descricaoNarrativa().contains("visitante")) {
                        return envolvidos.stream().allMatch(adversario.ids()::contains);
                    }
                    return envolvidos.isEmpty();
                }));
            }
            winRates[levelIndex] = wins / 1_000.0;
        }
        assertTrue(winRates[0] < winRates[1] && winRates[1] < winRates[2] && winRates[2] < winRates[3],
                "positional squad win rates: " + java.util.Arrays.toString(winRates));
        System.out.println("BALANCE 4-4-2-positional-win-rates=" + java.util.Arrays.toString(winRates));
    }

    @Test
    void positionalGoalAttributionFavorsFinishingRoles() {
        Squad equipe = squad(65);
        java.util.Map<Posicao, Long> golsPorPosicao = new java.util.EnumMap<>(Posicao.class);
        for (long seed = 0; seed < 10_000; seed++) {
            motor.simular(equipe.forca(), equipe.forca(), equipe.elenco(), equipe.elenco(), seed).eventos().stream()
                    .filter(evento -> evento.tipo() == TipoEvento.GOL)
                    .flatMap(evento -> evento.jogador().stream())
                    .forEach(jogador -> golsPorPosicao.merge(jogador.posicao(), 1L, Long::sum));
        }
        long total = golsPorPosicao.values().stream().mapToLong(Long::longValue).sum();
        double atacantes = golsPorPosicao.getOrDefault(Posicao.ATA, 0L) / (double) total;
        double goleiros = golsPorPosicao.getOrDefault(Posicao.GOL, 0L) / (double) total;
        System.out.println("BALANCE goal-share-by-position=" + golsPorPosicao);
        assertTrue(total > 10_000);
        assertTrue(atacantes > 0.30, "striker goal share: " + atacantes);
        assertTrue(goleiros < 0.03, "goalkeeper goal share: " + goleiros);
    }

    private static Squad squad(int level) {
        Formacao formacao = Formacao.quatroQuatroDois();
        List<Jogador> titulares = formacao.posicoesTitulares().stream()
                .map(posicao -> jogadorPosicional(posicao, level)).toList();
        List<Jogador> reservas = List.of(Posicao.GOL, Posicao.ZAG, Posicao.LAT, Posicao.MEI, Posicao.ATA)
                .stream().map(posicao -> jogadorPosicional(posicao, level - 2)).toList();
        Escalacao escalacao = new Escalacao(formacao, titulares, reservas);
        List<Jogador> elenco = java.util.stream.Stream.concat(escalacao.titulares().stream(),
                escalacao.reservas().stream()).toList();
        return new Squad(ForcaEquipe.aPartirDosJogadores(escalacao.titulares()), elenco,
                elenco.stream().map(Jogador::id).collect(java.util.stream.Collectors.toSet()));
    }

    private static Jogador jogadorPosicional(Posicao posicao, int nivel) {
        int tecnica = switch (posicao) { case GOL -> 42; case ZAG -> 50; case LAT -> 55; case VOL -> 58; case MEI -> 78; case ATA -> 65; };
        int fisico = switch (posicao) { case GOL -> 62; case ZAG, LAT, VOL, ATA -> 70; case MEI -> 58; };
        int mental = switch (posicao) { case GOL, ZAG, VOL -> 72; default -> 64; };
        int velocidade = switch (posicao) { case GOL -> 40; case ZAG -> 55; case LAT, ATA -> 78; case VOL -> 58; case MEI -> 66; };
        int finalizacao = switch (posicao) { case GOL -> 18; case ZAG, LAT, VOL -> 38; case MEI -> 60; case ATA -> 88; };
        int passe = switch (posicao) { case GOL -> 45; case ZAG -> 52; case LAT -> 65; case VOL -> 70; case MEI -> 82; case ATA -> 56; };
        int marcacao = switch (posicao) { case GOL -> 92; case ZAG -> 86; case LAT -> 72; case VOL -> 78; case MEI -> 48; case ATA -> 34; };
        return new Jogador(UUID.randomUUID(), "Jogador " + UUID.randomUUID(), LocalDate.of(2000, 1, 1), posicao,
                new AtributosJogador(escala(tecnica, nivel), escala(fisico, nivel), escala(mental, nivel),
                        escala(velocidade, nivel), escala(finalizacao, nivel), escala(passe, nivel),
                        escala(marcacao, nivel), escala(nivel, nivel)));
    }

    private static int escala(int valor, int nivel) {
        return Math.max(0, Math.min(100, (int) Math.round(valor * nivel / 60.0)));
    }

    private record Squad(ForcaEquipe forca, List<Jogador> elenco, java.util.Set<UUID> ids) { }

    @Test
    void enrichedSimulationNarratesPlayersAndAdditionalEventTypes() {
        List<Jogador> jogadores = List.of(jogador("Atleta 1"), jogador("Atleta 2"), jogador("Atleta 3"));
        long eventosEnriquecidos = 0;
        boolean encontrouNarracaoComNome = false;

        for (long seed = 0; seed < 1_000; seed++) {
            ResultadoSimulacao resultado = motor.simular(equipeMedia, equipeMedia, jogadores, jogadores, seed);
            eventosEnriquecidos += resultado.eventos().stream()
                    .filter(evento -> evento.tipo().name().matches("CARTAO_AMARELO|CARTAO_VERMELHO|LESAO|SUBSTITUICAO"))
                    .count();
            if (resultado.narracao().contains("Atleta")) {
                encontrouNarracaoComNome = true;
            }
        }

        assertTrue(eventosEnriquecidos > 0);
        assertTrue(encontrouNarracaoComNome);
    }

    @Test
    void applyingSimulationTransitionsMatchAndCopiesResult() {
        Partida partida = new Partida(UUID.randomUUID(),
                new Clube(UUID.randomUUID(), "Mandante", "MAN"),
                new Clube(UUID.randomUUID(), "Visitante", "VIS"), LocalDateTime.now());
        ResultadoSimulacao resultado = motor.simular(equipeMedia, equipeMedia, 42L);

        resultado.aplicarA(partida);

        assertEquals(StatusPartida.ENCERRADA, partida.status());
        assertEquals(resultado.golsMandante(), partida.golsMandante());
        assertEquals(resultado.golsVisitante(), partida.golsVisitante());
        assertEquals(resultado.eventos(), partida.eventos());
        assertTrue(partida.eventos().stream().allMatch(evento -> evento.tipo() != null));
        org.junit.jupiter.api.Assertions.assertThrows(IllegalStateException.class, () -> resultado.aplicarA(partida));
    }

    @Test
    void substitutionsIdentifyDistinctPlayersEnteringAndLeaving() {
        List<Jogador> jogadores = List.of(jogador("Titular"), jogador("Reserva"));

        ResultadoSimulacao resultado = java.util.stream.LongStream.range(0, 1_000)
                .mapToObj(seed -> motor.simular(equipeMedia, equipeMedia, jogadores, jogadores, seed))
                .filter(simulacao -> simulacao.eventos().stream().anyMatch(evento -> evento.tipo() == TipoEvento.SUBSTITUICAO))
                .findFirst().orElseThrow();

        var substituicao = resultado.eventos().stream()
                .filter(evento -> evento.tipo() == TipoEvento.SUBSTITUICAO)
                .findFirst().orElseThrow();
        assertTrue(substituicao.jogadorSai().isPresent());
        assertTrue(substituicao.jogadorEntra().isPresent());
        assertTrue(substituicao.jogadorSai().get() != substituicao.jogadorEntra().get());
    }

    private static RatingJogador rating(int valor) {
        return new RatingJogador(valor, valor, valor, valor, valor, valor, valor, valor);
    }

    private static Jogador jogador(String nome) {
        return new Jogador(UUID.randomUUID(), nome, LocalDate.of(2000, 1, 1), Posicao.MEI,
                new AtributosJogador(60, 60, 60, 60, 60, 60, 60, 60));
    }
}
