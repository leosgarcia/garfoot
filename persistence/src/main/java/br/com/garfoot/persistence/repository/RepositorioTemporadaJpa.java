package br.com.garfoot.persistence.repository;

import br.com.garfoot.core.model.campeonato.Campeonato;
import br.com.garfoot.core.application.port.RepositorioTemporada;
import br.com.garfoot.persistence.entity.TemporadaSalvaEntity;
import br.com.garfoot.persistence.entity.BackupTemporadaEntity;
import br.com.garfoot.persistence.mapper.TemporadaMapper;
import jakarta.persistence.EntityManager;
import jakarta.persistence.EntityManagerFactory;

import java.util.Objects;
import java.util.Optional;
import java.util.UUID;
import java.time.Instant;
import java.util.List;

public final class RepositorioTemporadaJpa implements RepositorioTemporada {
    private final EntityManagerFactory entityManagerFactory;
    private final TemporadaMapper mapper;

    public RepositorioTemporadaJpa(EntityManagerFactory entityManagerFactory) {
        this(entityManagerFactory, new TemporadaMapper());
    }

    public RepositorioTemporadaJpa(EntityManagerFactory entityManagerFactory, TemporadaMapper mapper) {
        this.entityManagerFactory = Objects.requireNonNull(entityManagerFactory, "entityManagerFactory must not be null");
        this.mapper = Objects.requireNonNull(mapper, "mapper must not be null");
    }

    @Override
    public void salvar(Campeonato campeonato) {
        TemporadaSalvaEntity entity = mapper.toEntity(Objects.requireNonNull(campeonato, "campeonato must not be null"));
        EntityManager manager = entityManagerFactory.createEntityManager();
        try {
            manager.getTransaction().begin();
            TemporadaSalvaEntity anterior = manager.find(TemporadaSalvaEntity.class, entity.getId());
            if (anterior != null) manager.persist(new BackupTemporadaEntity(UUID.randomUUID(), anterior.getId(),
                    Instant.now(), anterior.getEstadoJson()));
            manager.merge(entity);
            manager.getTransaction().commit();
        } catch (RuntimeException exception) {
            if (manager.getTransaction().isActive()) manager.getTransaction().rollback();
            throw exception;
        } finally {
            manager.close();
        }
    }

    public List<UUID> listarIds() {
        EntityManager manager = entityManagerFactory.createEntityManager();
        try { return manager.createQuery("select t.id from TemporadaSalvaEntity t order by t.nome", UUID.class).getResultList(); }
        finally { manager.close(); }
    }

    @Override
    public Optional<Campeonato> carregar(UUID id) {
        EntityManager manager = entityManagerFactory.createEntityManager();
        try {
            TemporadaSalvaEntity entity = manager.find(TemporadaSalvaEntity.class,
                    Objects.requireNonNull(id, "id must not be null"));
            if (entity == null) return Optional.empty();
            try { return Optional.of(mapper.toDomain(entity)); }
            catch (RuntimeException saveCorrompido) {
                List<BackupTemporadaEntity> backups = manager.createQuery(
                        "select b from BackupTemporadaEntity b where b.temporadaId = :id order by b.criadoEm desc",
                        BackupTemporadaEntity.class).setParameter("id", id).getResultList();
                for (BackupTemporadaEntity backup : backups) {
                    try { return Optional.of(mapper.toDomain(new TemporadaSalvaEntity(id, entity.getNome(), backup.getEstadoJson()))); }
                    catch (RuntimeException ignorado) { /* Try the preceding snapshot. */ }
                }
                throw new IllegalStateException("save is corrupted and no valid backup was found", saveCorrompido);
            }
        } finally {
            manager.close();
        }
    }
}
