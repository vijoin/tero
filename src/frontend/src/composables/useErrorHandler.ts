import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from 'vue-toastification'
import { PrimeIcons } from '@primevue/core'
import { findManifest, HttpError } from '@/services/api'
import ToastMessage from '@/components/common/ToastMessage.vue'

export function useErrorHandler() {
  const router = useRouter()
  const toast = useToast()
  const { t, mergeLocaleMessage } = useI18n({ useScope: 'global' })

  const handleError = async (error: unknown) => {
    if (error instanceof HttpError) {
      if (error.status === 401) {
        router.push('/logout')
        return
      }
      else if (error.status === 403) {
        router.push('/unauthorized')
        return
      }
      else if (error.status === 404) {
        router.push('/not-found')
        return
      }
    }
    console.error(error)
    const manifest = await findManifest()
    const text = t('internalError', { contactLink: `mailto:${manifest.contactEmail}?subject=Tero%20Error`, contactAddress: manifest.contactEmail })
    toast.error({ component: ToastMessage, props: { message: text } }, { icon: PrimeIcons.EXCLAMATION_CIRCLE })
  }

  mergeLocaleMessage('en', {
    internalError: 'There was some internal error. Try reloading the page and if the issue persists contact support [({contactAddress})]({contactLink}).'
  })
  mergeLocaleMessage('es', {
    internalError: 'Hubo un error interno. Intente recargar la página y si el problema persiste contacte a soporte [({contactAddress})]({contactLink}).'
  })

  return { handleError }
}
