package br.com.garfoot.persistence.repository;

import br.com.garfoot.core.engine.MotorCampeonato;
import br.com.garfoot.core.model.campeonato.Campeonato;
import br.com.garfoot.core.model.campeonato.TipoCompeticao;
import br.com.garfoot.core.model.clube.Clube;
import br.com.garfoot.persistence.FabricaPersistencia;
import jakarta.persistence.EntityManagerFactory;
import jakarta.persistence.Persistence;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;
import java.util.UUID;
import java.nio.file.Files;
import java.nio.file.Path;
import java.io.IOException;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertThrows;

class RepositorioTemporadaJpaTest {
    @Test
    void localFileDatabaseKeepsSeasonAfterFactoryRestart() throws IOException {
        Path diretorio = Files.createTempDirectory("garfoot-save-test");
        String url = "jdbc:h2:file:" + diretorio.resolve("temporada") + ";DB_CLOSE_ON_EXIT=FALSE";
        Campeonato temporada = new Campeonato(UUID.randomUUID(), "Save local", TipoCompeticao.LIGA);
        temporada.adicionarParticipante(new Clube(UUID.randomUUID(), "Clube Local", "LOC"));
        try {
            EntityManagerFactory primeiro = FabricaPersistencia.criar(url, "sa", "");
            new RepositorioTemporadaJpa(primeiro).salvar(temporada);
            primeiro.close();

            EntityManagerFactory segundo = FabricaPersistencia.criar(url, "sa", "");
            try {
                Campeonato carregada = new RepositorioTemporadaJpa(segundo).carregar(temporada.id()).orElseThrow();
                assertEquals("Save local", carregada.nome());
                assertEquals("Clube Local", carregada.participantes().getFirst().nome());
            } finally {
                segundo.close();
            }
        } finally {
            try (var arquivos = Files.walk(diretorio)) {
                arquivos.sorted(java.util.Comparator.reverseOrder()).forEach(caminho -> {
                    try { Files.deleteIfExists(caminho); }
                    catch (IOException exception) { throw new IllegalStateException(exception); }
                });
            }
        }
    }

    @Test
    void saveAndLoadPreservesSeasonCalendarResultsAndStandings() {
        EntityManagerFactory factory = Persistence.createEntityManagerFactory("garfoot-test");
        try {
            Campeonato temporada = new Campeonato(UUID.randomUUID(), "Liga de Teste", TipoCompeticao.LIGA);
            for (int i = 0; i < 4; i++) temporada.adicionarParticipante(
                    new Clube(UUID.randomUUID(), "Clube " + i, "C" + i));
            MotorCampeonato motor = new MotorCampeonato();
            motor.gerarTurnoEReturno(temporada, LocalDateTime.of(2026, 1, 1, 12, 0));
            motor.simularTemporada(temporada, 300L);

            RepositorioTemporadaJpa repositorio = new RepositorioTemporadaJpa(factory);
            repositorio.salvar(temporada);
            Campeonato carregada = repositorio.carregar(temporada.id()).orElseThrow();

            assertEquals(temporada.id(), carregada.id());
            assertEquals(temporada.rodadas().size(), carregada.rodadas().size());
            assertEquals(temporada.classificacao().stream().map(item -> item.pontos()).toList(),
                    carregada.classificacao().stream().map(item -> item.pontos()).toList());
            assertEquals(temporada.rodadas().stream().flatMap(r -> r.partidas().stream())
                            .map(p -> p.golsMandante() + ":" + p.golsVisitante() + ":" + p.status()).toList(),
                    carregada.rodadas().stream().flatMap(r -> r.partidas().stream())
                            .map(p -> p.golsMandante() + ":" + p.golsVisitante() + ":" + p.status()).toList());
            assertEquals(temporada.rodadas().stream().flatMap(r -> r.partidas().stream())
                            .flatMap(p -> p.eventos().stream()).map(e -> e.minuto() + ":" + e.tipo() + ":" + e.descricaoNarrativa()).toList(),
                    carregada.rodadas().stream().flatMap(r -> r.partidas().stream())
                            .flatMap(p -> p.eventos().stream()).map(e -> e.minuto() + ":" + e.tipo() + ":" + e.descricaoNarrativa()).toList());
            assertTrue(repositorio.carregar(UUID.randomUUID()).isEmpty());
        } finally {
            factory.close();
        }
    }

    @Test
    void corruptedCurrentSaveRecoversPreviousSnapshot() {
        EntityManagerFactory factory = Persistence.createEntityManagerFactory("garfoot-test");
        try {
            Campeonato season = new Campeonato(UUID.randomUUID(), "Temporada recuperável", TipoCompeticao.LIGA);
            season.adicionarParticipante(new Clube(UUID.randomUUID(), "Clube de backup", "BKP"));
            RepositorioTemporadaJpa repository = new RepositorioTemporadaJpa(factory);
            repository.salvar(season);
            season.adicionarParticipante(new Clube(UUID.randomUUID(), "Nova alteração", "NOV"));
            repository.salvar(season);

            var manager = factory.createEntityManager();
            manager.getTransaction().begin();
            manager.createQuery("update TemporadaSalvaEntity t set t.estadoJson = :json where t.id = :id")
                    .setParameter("json", "{broken").setParameter("id", season.id()).executeUpdate();
            manager.getTransaction().commit(); manager.close();

            Campeonato recovered = repository.carregar(season.id()).orElseThrow();
            assertEquals("Clube de backup", recovered.participantes().getFirst().nome());
            assertEquals(1, recovered.participantes().size());
        } finally { factory.close(); }
    }

    @Test
    void currentSnapshotFormatCanReadVersionOneWithoutNewFields() throws Exception {
        UUID seasonId = UUID.randomUUID();
        var entity = new br.com.garfoot.persistence.entity.TemporadaSalvaEntity(seasonId, "v1",
                """
                {"versaoFormato":1,"id":"%s","nome":"Liga antiga","tipo":"LIGA","clubes":[{"id":"%s","nome":"Clube antigo","sigla":"ANT","jogadores":[]}],"rodadas":[],"classificacao":[]}
                """.formatted(seasonId, UUID.randomUUID()));
        var parsed = new br.com.garfoot.persistence.mapper.TemporadaMapper().toDomain(entity);
        assertEquals("Liga antiga", parsed.nome());
    }
}
