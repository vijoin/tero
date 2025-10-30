<script setup lang="ts">
import { IconBell } from '@tabler/icons-vue';
import { ApiService, TeamRole, TeamRoleStatus } from '@/services/api';
import { onBeforeMount, ref } from 'vue';
import { loadUserProfile } from '@/composables/useUserProfile';
import { useErrorHandler } from '@/composables/useErrorHandler';

const api = new ApiService();
const { handleError } = useErrorHandler();

const invitations = ref<TeamRole[]>([]);
const popupRef = ref();

const emit = defineEmits<{
    (e: 'invitationAccepted'): void
}>();

onBeforeMount(async () => {
    try {
        const userProfile = await loadUserProfile();
        invitations.value = userProfile?.teams.filter(team => team.status === TeamRoleStatus.PENDING) ?? [];
    } catch (error) {
        handleError(error);
    }
});

const acceptInvitation = async (teamId: number) => {
    try {
        await api.acceptTeamInvitation(teamId);
        await loadUserProfile();
        invitations.value = invitations.value.filter(invitation => invitation.id !== teamId);
        emit('invitationAccepted');
        closeIfEmpty();
    } catch (error) {
        handleError(error);
    }
};

const rejectInvitation = async (teamId: number) => {
    try {
        await api.rejectTeamInvitation(teamId);
        invitations.value = invitations.value.filter(invitation => invitation.id !== teamId);
        closeIfEmpty();
    } catch (error) {
        handleError(error);
    }
};

const closeIfEmpty = () => {
    if (invitations.value.length === 0) {
        popupRef.value.hide();
    }
}

const togglePopup = (event: Event) => {
    popupRef.value.toggle(event);
}
</script>

<template>
    <div>
        <SimpleButton v-if="invitations.length > 0" @click="togglePopup($event)" class="relative">
            <IconBell />
            <span
                class="absolute bottom-[-0.15rem] right-[-0.15rem] text-xs bg-error text-white h-4 w-4 rounded-full flex items-center justify-center">
                {{ invitations.length }}
            </span>
        </SimpleButton>
    </div>
    <Popover ref="popupRef" class="w-130 max-h-100 overflow-y-auto">
        <NotificationItem v-for="invitation in invitations" :key="invitation.id" :invitation="invitation"
            @accept-invitation="acceptInvitation" @reject-invitation="rejectInvitation" />
    </Popover>
</template>
