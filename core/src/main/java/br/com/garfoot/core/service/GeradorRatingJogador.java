package br.com.garfoot.core.service;

import br.com.garfoot.core.model.jogador.DadosRatingJogador;
import br.com.garfoot.core.model.jogador.NivelCompetitivo;
import br.com.garfoot.core.model.jogador.Posicao;
import br.com.garfoot.core.model.jogador.RatingJogador;

public final class GeradorRatingJogador {
    private static final double MAX_RATING = 100.0;

    public RatingJogador gerar(DadosRatingJogador dados) {
        double mercado = mercado(dados.valorMercadoEur());
        double experiencia = experiencia(dados);
        double contribuicao = contribuicao(dados);
        double maturidade = maturidade(dados.idade());
        double fisicoBase = fisicoBase(dados);
        double prioridadePosicao = prioridadePosicao(dados.posicao());
        int[] ajustes = ajustesPorNivel(NivelCompetitivo.deValorMercado(dados.valorMercadoEur()));

        int tecnica = nota(mercado * 0.55 + contribuicao * 0.25 + experiencia * 0.20) + ajustes[0];
        int fisico = nota(fisicoBase * 0.65 + mercado * 0.20 + prioridadePosicao * 0.15) + ajustes[1];
        int mental = nota(experiencia * 0.45 + mercado * 0.30 + maturidade * 0.25) + ajustes[2];
        int velocidade = nota(fisicoBase * 0.55 + prioridadePosicao * 0.25 + maturidade * 0.10 + mercado * 0.10) + ajustes[3];
        int finalizacao = nota(contribuicao * 0.55 + tecnica * 0.25 + prioridadeFinalizacao(dados.posicao()) * 0.20) + ajustes[4];
        int passe = nota(tecnica * 0.45 + contribuicao * 0.20 + experiencia * 0.20 + prioridadePasse(dados.posicao()) * 0.15) + ajustes[5];
        int marcacao = nota(mercado * 0.25 + mental * 0.25 + fisico * 0.20 + prioridadeMarcacao(dados.posicao()) * 0.30) + ajustes[6];
        int potencial = nota(mercado * 0.45 + potencialIdade(dados.idade()) * 0.40 + maturidade * 0.15) + ajustes[7];

        return new RatingJogador(
            limitarNota(tecnica), limitarNota(fisico), limitarNota(mental), limitarNota(velocidade),
            limitarNota(finalizacao), limitarNota(passe), limitarNota(marcacao), limitarNota(potencial));
    }

    private double mercado(long valorMercadoEur) {
        return limitar(25.0 + 18.0 * Math.log10(1.0 + valorMercadoEur / 100_000.0));
    }

    private double experiencia(DadosRatingJogador dados) {
        double minutos = Math.min(40.0, dados.minutosJogador() / 500.0);
        double aparicoes = Math.min(15.0, dados.aparicoes() / 20.0);
        double internacional = Math.min(20.0, dados.internacionalCaps() * 0.8);
        return limitar(25.0 + minutos + aparicoes + internacional);
    }

    private double contribuicao(DadosRatingJogador dados) {
        if (dados.minutosJogador() == 0) {
            return 35.0;
        }
        double fator90 = 90.0 / dados.minutosJogador();
        double golsPor90 = Math.min(1.2, dados.gols() * fator90);
        double assistenciasPor90 = Math.min(1.0, dados.assistencias() * fator90);
        return limitar(35.0 + golsPor90 * 22.0 + assistenciasPor90 * 16.0);
    }

    private double maturidade(int idade) {
        return limitar(58.0 - Math.abs(idade - 28) * 1.3);
    }

    private double fisicoBase(DadosRatingJogador dados) {
        double idade = 76.0 - Math.abs(dados.idade() - 27) * 1.25;
        double altura = 58.0 + (dados.alturaCm() - 175) * 0.35;
        return limitar(idade * 0.65 + altura * 0.35);
    }

    private double potencialIdade(int idade) {
        if (idade <= 21) {
            return 92.0;
        }
        if (idade <= 24) {
            return 84.0;
        }
        if (idade <= 28) {
            return 72.0;
        }
        if (idade <= 31) {
            return 58.0;
        }
        return 42.0;
    }

    private double prioridadePosicao(Posicao posicao) {
        return switch (posicao) {
            case GOL -> 62.0;
            case ZAG -> 58.0;
            case LAT -> 78.0;
            case VOL -> 65.0;
            case MEI -> 82.0;
            case ATA -> 86.0;
        };
    }

    private double prioridadeFinalizacao(Posicao posicao) {
        return switch (posicao) {
            case GOL, ZAG, LAT, VOL -> 42.0;
            case MEI -> 66.0;
            case ATA -> 86.0;
        };
    }

    private double prioridadePasse(Posicao posicao) {
        return switch (posicao) {
            case GOL -> 42.0;
            case ZAG -> 55.0;
            case LAT -> 66.0;
            case VOL -> 78.0;
            case MEI -> 88.0;
            case ATA -> 68.0;
        };
    }

    private double prioridadeMarcacao(Posicao posicao) {
        return switch (posicao) {
            case GOL -> 25.0;
            case ZAG -> 88.0;
            case LAT -> 78.0;
            case VOL -> 76.0;
            case MEI -> 48.0;
            case ATA -> 28.0;
        };
    }

    private int nota(double valor) {
        return (int) Math.round(limitar(valor));
    }

    private int limitarNota(int valor) {
        return (int) Math.round(limitar(valor));
    }

    private int[] ajustesPorNivel(NivelCompetitivo nivel) {
        return switch (nivel) {
            case ELITE -> new int[]{18, 6, 15, 8, 23, 15, 9, 12};
            case ALTO -> new int[]{23, 5, 20, 6, 20, 18, 11, 13};
            case PROFISSIONAL -> new int[]{24, 2, 18, 5, 15, 15, 9, 16};
            case DESENVOLVIMENTO -> new int[]{24, 0, 15, 3, 8, 12, 8, 16};
        };
    }

    private double limitar(double valor) {
        return Math.max(20.0, Math.min(MAX_RATING, valor));
    }
}
