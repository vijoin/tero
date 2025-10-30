<template>
  <PageLayout>
    <template v-slot:left>
      <SidebarPanel />
    </template>
    <template v-slot:right>
      <router-view />
    </template>
  </PageLayout>
</template>