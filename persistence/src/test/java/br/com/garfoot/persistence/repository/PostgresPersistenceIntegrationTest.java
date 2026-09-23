package br.com.garfoot.persistence.repository;

import br.com.garfoot.core.model.campeonato.Campeonato;
import br.com.garfoot.core.model.campeonato.TipoCompeticao;
import br.com.garfoot.core.model.clube.Clube;
import br.com.garfoot.persistence.FabricaPersistencia;
import jakarta.persistence.EntityManagerFactory;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;

import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;

class PostgresPersistenceIntegrationTest {
    @Test
    @EnabledIfEnvironmentVariable(named = "GARFOOT_TEST_POSTGRES_URL", matches = "jdbc:postgresql:.*")
    void savesAndLoadsSeasonUsingPostgresql() {
        EntityManagerFactory factory = FabricaPersistencia.criar(
                System.getenv("GARFOOT_TEST_POSTGRES_URL"),
                System.getenv().getOrDefault("GARFOOT_TEST_POSTGRES_USER", "garfoot_test"),
                System.getenv().getOrDefault("GARFOOT_TEST_POSTGRES_PASSWORD", ""));
        try {
            Campeonato temporada = new Campeonato(UUID.randomUUID(), "PostgreSQL integration", TipoCompeticao.LIGA);
            temporada.adicionarParticipante(new Clube(UUID.randomUUID(), "Banco", "DB"));
            RepositorioTemporadaJpa repositorio = new RepositorioTemporadaJpa(factory);
            repositorio.salvar(temporada);
            assertEquals("Banco", repositorio.carregar(temporada.id()).orElseThrow().participantes().getFirst().nome());
        } finally {
            factory.close();
        }
    }
}
