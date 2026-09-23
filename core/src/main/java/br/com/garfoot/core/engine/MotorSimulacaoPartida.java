package br.com.garfoot.core.engine;

import br.com.garfoot.core.model.partida.EventoPartida;
import br.com.garfoot.core.model.partida.TipoEvento;
import br.com.garfoot.core.model.jogador.Jogador;
import br.com.garfoot.core.model.tatica.Escalacao;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import java.util.random.RandomGenerator;
import java.util.random.RandomGeneratorFactory;

public final class MotorSimulacaoPartida {
    private static final int MINUTOS_PARTIDA = 90;
    private static final double MANDO_DE_CAMPO = 0.15;

    public ResultadoSimulacao simular(ForcaEquipe mandante, ForcaEquipe visitante, long seed) {
        return simular(mandante, visitante, List.of(), List.of(), seed);
    }

    public ResultadoSimulacao simular(
            ForcaEquipe mandante,
            ForcaEquipe visitante,
            List<Jogador> jogadoresMandante,
            List<Jogador> jogadoresVisitante,
            long seed) {
        Objects.requireNonNull(mandante, "mandante must not be null");
        Objects.requireNonNull(visitante, "visitante must not be null");
        Objects.requireNonNull(jogadoresMandante, "jogadoresMandante must not be null");
        Objects.requireNonNull(jogadoresVisitante, "jogadoresVisitante must not be null");
        RandomGenerator random = RandomGeneratorFactory.of("L64X128MixRandom").create(seed);
        double expectativaMandante = expectativa(mandante.ataque(), visitante.defesa(), MANDO_DE_CAMPO);
        double expectativaVisitante = expectativa(visitante.ataque(), mandante.defesa(), 0.0);
        int golsMandante = 0;
        int golsVisitante = 0;
        List<EventoPartida> eventos = new ArrayList<>();
        int substituicoesMandante = 0;
        int substituicoesVisitante = 0;

        for (int minuto = 1; minuto <= MINUTOS_PARTIDA; minuto++) {
            if (random.nextDouble() < expectativaMandante / MINUTOS_PARTIDA) {
                golsMandante++;
                eventos.add(eventoGol(minuto, jogadoresMandante, random, "Gol do mandante"));
            }
            if (random.nextDouble() < expectativaVisitante / MINUTOS_PARTIDA) {
                golsVisitante++;
                eventos.add(eventoGol(minuto, jogadoresVisitante, random, "Gol do visitante"));
            }
            adicionarEventosDisciplinares(minuto, jogadoresMandante, random, eventos, "mandante");
            adicionarEventosDisciplinares(minuto, jogadoresVisitante, random, eventos, "visitante");
            if (minuto >= 55 && substituicoesMandante < 3 && random.nextDouble() < 0.035) {
                eventos.add(substituicao(minuto, jogadoresMandante, random, "mandante"));
                substituicoesMandante++;
            }
            if (minuto >= 55 && substituicoesVisitante < 3 && random.nextDouble() < 0.035) {
                eventos.add(substituicao(minuto, jogadoresVisitante, random, "visitante"));
                substituicoesVisitante++;
            }
        }

        eventos.sort(Comparator.comparingInt(EventoPartida::minuto));
        return new ResultadoSimulacao(golsMandante, golsVisitante, eventos);
    }

    public ResultadoSimulacao simular(ForcaEquipe mandante, ForcaEquipe visitante,
                                      Escalacao escalacaoMandante, Escalacao escalacaoVisitante, long seed) {
        Objects.requireNonNull(escalacaoMandante, "escalacaoMandante must not be null");
        Objects.requireNonNull(escalacaoVisitante, "escalacaoVisitante must not be null");
        RandomGenerator random = RandomGeneratorFactory.of("L64X128MixRandom").create(seed);
        double expectativaMandante = expectativa(mandante.ataque(), visitante.defesa(), MANDO_DE_CAMPO);
        double expectativaVisitante = expectativa(visitante.ataque(), mandante.defesa(), 0.0);
        ElencoEmCampo equipeMandante = new ElencoEmCampo(escalacaoMandante);
        ElencoEmCampo equipeVisitante = new ElencoEmCampo(escalacaoVisitante);
        List<EventoPartida> eventos = new ArrayList<>();
        for (int minuto = 1; minuto <= MINUTOS_PARTIDA; minuto++) {
            if (random.nextDouble() < expectativaMandante / MINUTOS_PARTIDA)
                eventos.add(eventoGol(minuto, equipeMandante.emCampo, random, "Gol do mandante"));
            if (random.nextDouble() < expectativaVisitante / MINUTOS_PARTIDA)
                eventos.add(eventoGol(minuto, equipeVisitante.emCampo, random, "Gol do visitante"));
            adicionarEventosDisciplinares(minuto, equipeMandante.emCampo, random, eventos, "mandante");
            adicionarEventosDisciplinares(minuto, equipeVisitante.emCampo, random, eventos, "visitante");
            if (minuto >= 55) {
                substituirSePossivel(minuto, equipeMandante, random, eventos, "mandante");
                substituirSePossivel(minuto, equipeVisitante, random, eventos, "visitante");
            }
        }
        eventos.sort(Comparator.comparingInt(EventoPartida::minuto));
        return new ResultadoSimulacao((int) eventos.stream().filter(e -> e.tipo() == TipoEvento.GOL && e.descricaoNarrativa().contains("mandante")).count(),
                (int) eventos.stream().filter(e -> e.tipo() == TipoEvento.GOL && e.descricaoNarrativa().contains("visitante")).count(), eventos);
    }

    private void substituirSePossivel(int minuto, ElencoEmCampo equipe, RandomGenerator random,
                                      List<EventoPartida> eventos, String lado) {
        if (equipe.substituicoes >= 3 || equipe.banco.isEmpty() || random.nextDouble() >= 0.035) return;
        Jogador sai = equipe.emCampo.remove(random.nextInt(equipe.emCampo.size()));
        Jogador entra = equipe.banco.remove(random.nextInt(equipe.banco.size()));
        equipe.emCampo.add(entra);
        equipe.substituicoes++;
        eventos.add(new EventoPartida(minuto, TipoEvento.SUBSTITUICAO, sai,
                "Substituição: " + sai.nome() + " sai e " + entra.nome() + " entra pelo " + lado, sai, entra));
    }

    private static final class ElencoEmCampo {
        private final List<Jogador> emCampo;
        private final List<Jogador> banco;
        private int substituicoes;
        private ElencoEmCampo(Escalacao escalacao) {
            emCampo = new ArrayList<>(escalacao.titulares());
            banco = new ArrayList<>(escalacao.reservas());
        }
    }

    private void adicionarEventosDisciplinares(
            int minuto,
            List<Jogador> jogadores,
            RandomGenerator random,
            List<EventoPartida> eventos,
            String lado) {
        if (random.nextDouble() < 0.018) {
            eventos.add(eventoComJogador(minuto, TipoEvento.CARTAO_AMARELO, jogadores, random,
                    "Cartão amarelo para jogador do " + lado));
        }
        if (random.nextDouble() < 0.001) {
            eventos.add(eventoComJogador(minuto, TipoEvento.CARTAO_VERMELHO, jogadores, random,
                    "Cartão vermelho para jogador do " + lado));
        }
        if (random.nextDouble() < 0.004) {
            eventos.add(eventoComJogador(minuto, TipoEvento.LESAO, jogadores, random,
                    "Lesão de jogador do " + lado));
        }
    }

    private EventoPartida substituicao(int minuto, List<Jogador> jogadores, RandomGenerator random, String lado) {
        if (jogadores.size() < 2) {
            return new EventoPartida(minuto, TipoEvento.SUBSTITUICAO, null,
                    "Substituição do " + lado);
        }
        int indiceSaida = random.nextInt(jogadores.size());
        int indiceEntrada = random.nextInt(jogadores.size() - 1);
        if (indiceEntrada >= indiceSaida) {
            indiceEntrada++;
        }
        Jogador sai = jogadores.get(indiceSaida);
        Jogador entra = jogadores.get(indiceEntrada);
        return new EventoPartida(minuto, TipoEvento.SUBSTITUICAO, sai,
                "Substituição: " + sai.nome() + " sai e " + entra.nome() + " entra pelo " + lado, sai, entra);
    }

    private EventoPartida eventoComJogador(
            int minuto,
            TipoEvento tipo,
            List<Jogador> jogadores,
            RandomGenerator random,
            String descricaoGenerica) {
        if (jogadores.isEmpty()) {
            return new EventoPartida(minuto, tipo, null, descricaoGenerica);
        }
        Jogador jogador = jogadores.get(random.nextInt(jogadores.size()));
        return new EventoPartida(minuto, tipo, jogador, descricaoGenerica + ": " + jogador.nome());
    }

    private EventoPartida eventoGol(int minuto, List<Jogador> jogadores, RandomGenerator random, String descricao) {
        if (jogadores.isEmpty()) {
            return new EventoPartida(minuto, TipoEvento.GOL, null, descricao);
        }
        double pesoTotal = jogadores.stream().mapToDouble(MotorSimulacaoPartida::pesoFinalizacao).sum();
        double sorteio = random.nextDouble() * pesoTotal;
        for (Jogador jogador : jogadores) {
            sorteio -= pesoFinalizacao(jogador);
            if (sorteio < 0) {
                return new EventoPartida(minuto, TipoEvento.GOL, jogador, descricao + ": " + jogador.nome());
            }
        }
        Jogador ultimo = jogadores.getLast();
        return new EventoPartida(minuto, TipoEvento.GOL, ultimo, descricao + ": " + ultimo.nome());
    }

    private static double pesoFinalizacao(Jogador jogador) {
        double prioridadePosicional = switch (jogador.posicao()) {
            case GOL -> 0.10;
            case ZAG -> 0.65;
            case LAT -> 0.85;
            case VOL -> 0.90;
            case MEI -> 1.15;
            case ATA -> 1.35;
        };
        double ratingOfensivo = 1 + jogador.atributos().finalizacao() * 0.8 + jogador.atributos().tecnica() * 0.2;
        return prioridadePosicional * ratingOfensivo;
    }

    private double expectativa(double ataque, double defesaAdversaria, double mando) {
        return limitar(0.72 + ataque * 0.012 - defesaAdversaria * 0.006 + mando, 0.15, 3.50);
    }

    private double limitar(double valor, double minimo, double maximo) {
        return Math.max(minimo, Math.min(maximo, valor));
    }
}
