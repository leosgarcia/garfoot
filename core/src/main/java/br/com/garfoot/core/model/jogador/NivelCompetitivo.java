package br.com.garfoot.core.model.jogador;

public enum NivelCompetitivo {
    ELITE,
    ALTO,
    PROFISSIONAL,
    DESENVOLVIMENTO;

    public static NivelCompetitivo deValorMercado(long valorMercadoEur) {
        if (valorMercadoEur >= 20_000_000) {
            return ELITE;
        }
        if (valorMercadoEur >= 5_000_000) {
            return ALTO;
        }
        if (valorMercadoEur >= 500_000) {
            return PROFISSIONAL;
        }
        return DESENVOLVIMENTO;
    }
}
