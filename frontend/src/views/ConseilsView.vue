<script setup lang="ts">
import Card from '@/components/AppCard.vue'
import Header from '@/components/AppHeader.vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { computed, onUnmounted, watchEffect } from 'vue'
import { conseilHebdo } from '@/data/conseilHebdo.ts'

const authStore = useAuthStore()
const router = useRouter()
const isConnected = computed(() => authStore.isConnected)

// Scroll lock si pas connecté
watchEffect(() => {
  if (!isConnected.value) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

// Scroll unlock au unmount
onUnmounted(() => {
  document.body.style.overflow = ''
})

// --- FONCTION UTILITAIRE : Récupérer le numéro de la semaine (1-52) ---
function getWeekNumber(d: Date): number {
  const date = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()))
  // On se cale sur le jeudi de la semaine actuelle (norme ISO 8601)
  date.setUTCDate(date.getUTCDate() + 4 - (date.getUTCDay() || 7))
  // On récupère le 1er janvier
  const yearStart = new Date(Date.UTC(date.getUTCFullYear(), 0, 1))
  // On calcule le numéro de semaine
  const weekNo = Math.ceil(((date.getTime() - yearStart.getTime()) / 86400000 + 1) / 7)
  return weekNo
}

const conseilActuel = computed(() => {
  const currentWeek = getWeekNumber(new Date())

  // L'index d'un tableau commence à 0, donc on fait -1.
  // Le modulo (%) permet de boucler : si on est semaine 53, ça revient au conseil 1.
  const index = (currentWeek - 1) % conseilHebdo.length

  return conseilHebdo[index]
})
</script>

<template>
  <div class="dashboard-wrapper">
    <Header title="Conseils" />
    <div class="scrollable-area">
      <div v-if="!isConnected" class="blur-overlay">
        <div class="lock-message">
          <span class="lock-icon">🔒</span>
          <p>Connectez-vous pour accéder aux conseils</p>
          <button @click="router.push('/login')" class="login-btn">Se connecter</button>
        </div>
      </div>
      <div :class="{ 'blurred-content': !isConnected }">
        <!-- Conseil de la semaine -->
        <Card title="Conseil de la semaine">
          <div class="dashboard-card-content">
            <p class="dashboard-text">{{ conseilActuel }}</p>
          </div>
        </Card>

        <!-- Le saviez-vous -->
        <Card title="Le saviez-vous ?">
          <div class="dashboard-card-content">
            <p class="dashboard-text">
              Il n'y a pas que l'empreinte carbone qui importe, l'empreinte eau est aussi importante
              ! Ces deux empreintes sont complémentaires pour la gestion des ressources naturelles
              de la planète.
            </p>
          </div>
        </Card>

        <!-- Aide du gouvernement -->
        <Card title="Conseils du gouvernement">
          <div class="dashboard-card-content gov-links-container">
            <a
              href="https://www.economie.gouv.fr/particuliers/mes-droits-conso/bien-consommer/tout-savoir-sur-lindice-de-durabilite#"
              target="_blank"
              class="emoji-link"
              title="Visiter le site"
            >
              <p class="aide_text">Indice de durabilité 🔗</p>
            </a>

            <a
              href="https://www.economie.gouv.fr/particuliers/mes-droits-conso/bien-consommer/tout-savoir-sur-lindice-de-reparabilite"
              target="_blank"
              class="emoji-link"
              title="Visiter le site"
            >
              <p class="aide_text">Indice de réparabilité 🔗</p>
            </a>

            <a
              href="https://www.economie.gouv.fr/particuliers/mes-droits-conso/bien-consommer/bonus-reparation-comment-ca-marche"
              target="_blank"
              class="emoji-link"
              title="Visiter le site"
            >
              <p class="aide_text">Bonus de réparation 🔗</p>
            </a>
          </div>
        </Card>
      </div>
    </div>
  </div>
</template>

<style scoped>

.login-btn {
  background-color: #679436;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  font-size: 1rem;
}

.dashboard-card-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 10px 0;
  text-align: center;
}

.dashboard-text {
  font-size: 1rem;
  color: #666;
  font-weight: 500;
  max-width: 100%;
}

.aide_text {
  font-size: 1.2rem;
  font-weight: 600;
  color: #666;
  text-decoration: underline;
}

.emoji-link {
  font-size: 2rem; /* Taille de l'emoji */
  text-decoration: none; /* Enlève le soulignement bleu moche */
  display: inline-block; /* Permet la transformation */
}

/* --- SÉPARATEURS POUR LES LIENS GOUVERNEMENT --- */

/* On force le conteneur à prendre toute la largeur et on retire le gap par défaut */
.gov-links-container {
  width: 100%;
  gap: 0 !important; /* On retire l'espace par défaut pour gérer nous-mêmes le padding */
  padding-top: 0;
  padding-bottom: 0;
}

/* Style spécifique pour ces liens */
.gov-links-container .emoji-link {
  width: 80%;
  padding: 15px 0; /* Espace vertical pour aérer */
  border-bottom: 3px solid #e0e0e0; /* La ligne de séparation grise claire */
  display: block; /* Important pour que la bordure fasse toute la largeur */
}

/* On retire la bordure du tout dernier lien pour faire propre */
.gov-links-container .emoji-link:last-child {
  border-bottom: none;
}

/* Petit ajustement pour le texte au survol */
.gov-links-container .emoji-link:hover {
  background-color: #f9f9f9; /* Optionnel : léger gris au survol */
}
</style>
