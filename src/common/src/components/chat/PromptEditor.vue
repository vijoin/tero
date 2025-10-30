<script lang="ts">

</script>

<script lang="ts" setup>
import { useI18n } from 'vue-i18n'
import { reactive, ref, computed  } from 'vue';
import { AgentPrompt } from '../../utils/domain';

const props = defineProps<{
    editingPrompt?: AgentPrompt,
    starter?: boolean,
    shareable?: boolean,
    sharedAgent?: boolean,
    newPromptText?: string,
    promptSaver: (prompt: AgentPrompt) => Promise<void>,
    errorHandler: (error: unknown) => void
}>()
const emit = defineEmits<{
    (e: 'close'): void
}>()

const { t } = useI18n();
const nameMaxLength = 50;
const prompt = reactive({
    name: props.editingPrompt?.name || "",
    instructions: props.editingPrompt?.content || props.newPromptText || "",
    visibility: props.editingPrompt?.shared || false
});
const originalPrompt = reactive({ ...prompt });
const showShareConfirmation = ref<boolean>(false)
const showCloseConfirmation = ref<boolean>(false)
const isModified = () => {
    return (
        prompt.name !== originalPrompt.name ||
        prompt.instructions !== originalPrompt.instructions ||
        prompt.visibility !== originalPrompt.visibility
    );
};
const submitting = ref<boolean>(false)

const onClose = () => {
    if (isModified()) {
        showCloseConfirmation.value = true;
    } else {
        emit("close");
    }
}

const confirmPrompt = async () => {
    submitting.value = true;
    const payload = {
        name: prompt.name,
        content: prompt.instructions,
        shared: props.starter || prompt.visibility,
        starter: props.starter || false
    }
    try {
        await props.promptSaver(props.editingPrompt? {...props.editingPrompt, ...payload} : payload as AgentPrompt)
        emit("close")
    } catch (e) {
        props.errorHandler(e)
    } finally {
        submitting.value = false;
    }
}

const onCancelShare = async () => {
    showShareConfirmation.value = false;
    prompt.visibility = !prompt.visibility;
}

const onConfirmShare = async () => {
    showShareConfirmation.value = false;
}

const title = computed(() => {
    return props.starter ?
        (props.editingPrompt ? t('editStarterTitle') : t('createStarterTitle')) :
        (props.editingPrompt ? t('editPromptTitle') : t('createPromptTitle'))
})

const onShowShareConfirmation = () => {
    showShareConfirmation.value = true;
}
</script>

<template>
    <FlexCard>
        <template #header>
            <div class="flex w-full items-center pb-3 justify-between">
                <div class="flex gap-2 items-center">
                    <IconPlayerPlay v-if="starter" />
                    <IconBook2 v-else />
                    <span class="text-lg">{{ title }}</span>
                </div>
                <div>
                    <SimpleButton @click="onClose">
                        <IconX />
                    </SimpleButton>
                </div>
            </div>
        </template>
        <div class="flex flex-col w-full gap-3 pb-4">
            <div class="form-field flex flex-col flex-grow gap-2">
                <label for="name">{{ t('name') }}</label>
                <InteractiveInput v-model="prompt.name" name="name" type="text" id="name" :placeholder="t('namePlaceholder')" :required="true"
                    :maxlength="nameMaxLength" />
            </div>
            <div class="form-field flex flex-col gap-2">
                <label for="instructions">{{ t('instructions') }}</label>
                <InteractiveInput v-model="prompt.instructions" name="instructions" :autoResize="true" :maxHeight="150" :rows="3" :placeholder="t('instructionsPlaceholder')" id="instructions" :required="true" />
                <span class="text-sm">{{ t('inputParameterDescription') }}</span>
            </div>
            <div v-if="!starter && shareable" class="form-field flex flex-col gap-2">
                <label for="visibility">{{ t('visibility') }}</label>
                <div class="flex items-center gap-2">
                    <ToggleSwitch v-model="prompt.visibility" name="visibility" id="visibility" @change="onShowShareConfirmation"/>
                    <span>{{ prompt.visibility === true ? t('makePrivate') : t('makePublic') }}</span>
                </div>
            </div>
            <div class="flex justify-end">
                <SimpleButton @click="confirmPrompt" :disabled="submitting || !prompt.name || !prompt.instructions || prompt.name.length > nameMaxLength" class="px-6" variant="primary" shape="rounded">
                   {{ t('confirmButton') }}
                </SimpleButton>
            </div>
        </div>
    </FlexCard>

    <Dialog v-model:visible="showCloseConfirmation"
        :header="t('closeConfirmTitle')" :modal="true"
        :draggable="false" :resizable="false" :closable="false" class="max-w-150">
        <div class="flex flex-col gap-5">
            <div class="flex flex-row gap-2 items-start whitespace-pre-line">
                {{ t('closeConfirmDescription') }}
            </div>
            <div class="flex flex-row gap-2 justify-end">
                <SimpleButton @click="showCloseConfirmation = false" shape="square" variant="secondary">{{ t('continueEditButton') }}</SimpleButton>
                <SimpleButton @click="emit('close')" shape="square" variant="error">{{ t('discardChangesButton') }}</SimpleButton>
            </div>
        </div>
    </Dialog>

    <Dialog v-model:visible="showShareConfirmation"
        :header="t(prompt?.visibility ? 'shareConfirmationTitle' : 'unshareConfirmationTitle')" :modal="true"
        :draggable="false" :resizable="false" :closable="false" class="max-w-150">
        <div class="flex flex-col gap-5">
            <div class="flex flex-row gap-2 items-start whitespace-pre-line">
                {{ t(prompt.visibility ? sharedAgent ?
                    'shareSharedAgentConfirmationMessage' : 'sharePrivateAgentConfirmationMessage' :
                    'unshareConfirmationMessage')
                }}
            </div>
            <div class="flex flex-row gap-2 justify-end">
                <SimpleButton @click="onCancelShare" shape="square" variant="secondary">{{ t('cancel') }}</SimpleButton>
                <SimpleButton @click="onConfirmShare" variant="primary" shape="square">{{ t(prompt.visibility ? 'publish' : 'unpublish') }}</SimpleButton>
            </div>
        </div>
    </Dialog>
</template>

<i18n lang="json">
    {
      "en": {
        "createPromptTitle": "Create prompt",
        "createStarterTitle": "Create starter",
        "editPromptTitle": "Edit prompt",
        "editStarterTitle": "Edit starter",
        "name": "Name",
        "namePlaceholder": "Type the name",
        "instructions": "Instructions",
        "instructionsPlaceholder": "Type the instructions",
        "visibility": "Visibility",
        "makePublic": "Make public",
        "makePrivate": "Make private",
        "confirmButton": "Confirm",
        "inputParameterDescription": "Use {'{'}{'{'} Variable name {'}'}{'}'} syntax to parameterize the instructions",
        "shareConfirmationTitle": "Do you want to make this prompt public?",
        "unshareConfirmationTitle": "Do you want to make this prompt private?",
        "shareSharedAgentConfirmationMessage": "When you make a prompt public it will be visible to everyone using this agent.\n\nAdditionally, all future modifications to the prompt will be immediately available to the rest of the users.",
        "sharePrivateAgentConfirmationMessage": "When you make a prompt public it will be visible to everyone using this agent, once the agent is made public.\n\nAdditionally, all future modifications to the prompt will be immediately available to the rest of the users.",
        "unshareConfirmationMessage": "When you make a prompt private it will no longer be visible to other users.",
        "unpublish": "Make private",
        "publish": "Publish",
        "cancel": "Cancel",
        "closeConfirmTitle": "Discard changes?",
        "closeConfirmDescription": "You have unsaved edits to this prompt. If you close now, all changes will be lost.",
        "continueEditButton": "Continue editing",
        "discardChangesButton": "Discard changes"
    },
      "es": {
        "createPromptTitle": "Crear prompt",
        "createStarterTitle": "Crear iniciador",
        "editPromptTitle": "Editar prompt",
        "editStarterTitle": "Editar iniciador",
        "name": "Nombre",
        "namePlaceholder": "Ingresa el nombre",
        "instructions": "Instrucciones",
        "instructionsPlaceholder": "Escribe las instrucciones",
        "visibility": "Visibilidad",
        "makePublic": "Hacer publico",
        "makePrivate": "Hacer privado",
        "confirmButton": "Confirmar",
        "inputParameterDescription": "Usa {'{'}{'{'} Nombre de variable {'}'}{'}'} para parametrizar las instrucciones",
        "shareConfirmationTitle": "¿Quieres hacer este prompt público?",
        "unshareConfirmationTitle": "¿Quieres hacer este prompt privado?",
        "shareSharedAgentConfirmationMessage": "Cuando haces un prompt público, este será visible para todos los que utilicen el agente.\n\nAdemás, todas las modificaciones futuras al prompt estarán disponibles inmediatamente para el resto de sus usuarios.",
        "sharePrivateAgentConfirmationMessage": "Cuando haces un prompt público, este será visible para todos los que utilicen el agente, una vez que el agente sea público.\n\nAdemás, todas las modificaciones futuras al prompt estarán disponibles inmediatamente para el resto de sus usuarios.",
        "unshareConfirmationMessage": "Cuando haces un prompt privado ya no será visible para el resto de usuarios.",
        "unpublish": "Hacer privado",
        "publish": "Publicar",
        "cancel": "Cancelar",
        "closeConfirmTitle": "¿Descartar cambios?",
        "closeConfirmDescription": "Tienes cambios sin guardar en este prompt. Si cierras ahora, todos los cambios se perderán.",
        "continueEditButton": "Seguir editando",
        "discardChangesButton": "Descartar"
    }
}
</i18n>
