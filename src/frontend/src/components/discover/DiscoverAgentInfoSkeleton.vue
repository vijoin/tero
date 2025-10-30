<template>
  <div class="animate-pulse space-y-6 min-h-[475px]">
    <div class="flex items-center gap-2 justify-between w-full pb-5 pt-5 border-b border-auxiliar-gray animate-pulse">
      <div class="flex flex-row gap-2 items-center flex-1 min-w-0">
        <div class="h-12 w-12 rounded-full bg-gray-300"></div>
        <div class="flex flex-col gap-1 min-w-0">
          <div class="h-6 w-40 bg-gray-300 rounded"></div>
          <div class="flex gap-1 text-xs w-fit">
            <div class="h-3 w-24 bg-gray-300 rounded"></div>
            <div class="h-3 w-3 bg-gray-300 rounded"></div>
            <div class="h-3 w-20 bg-gray-300 rounded"></div>
          </div>
        </div>
      </div>
      <div class="flex flex-row gap-4 justify-start h-full self-start flex-shrink-0">
        <div class="h-8 w-[100.16px] bg-gray-300 rounded"></div>
        <div class="h-8 w-[134.69px] bg-gray-300 rounded"></div>
        <div class="h-8 w-8 bg-gray-300 rounded-full"></div>
      </div>
    </div>


    <div class="flex flex-col gap-6 animate-pulse">
      <div class="h-6 w-3/4 bg-gray-300 rounded"></div>

      <div class="flex flex-row gap-2 bg-pale p-2 px-8 rounded-md items-center justify-between h-12">
        <div class="flex flex-row gap-4 items-center">
          <div class="h-4 w-16 bg-gray-300 rounded"></div>
          <div class="h-8 w-24 bg-gray-300 rounded"></div>
        </div>
        <div class="flex flex-row gap-4 items-center">
          <div class="h-4 w-16 bg-gray-300 rounded"></div>
          <div class="h-8 w-24 bg-gray-300 rounded"></div>
        </div>
        <div class="flex flex-row gap-4 items-center">
          <div class="h-4 w-16 bg-gray-300 rounded"></div>
          <div class="h-8 w-12 bg-gray-300 rounded"></div>
        </div>
      </div>

      <div class="form-field relative gap-2">
        <div class="h-6 w-32 bg-gray-300 rounded mb-2"></div>
        <div class="h-[178px] bg-gray-300 rounded"></div>
      </div>

      <div class="form-field relative gap-2">
        <div class="h-6 w-24 bg-gray-300 rounded mb-2"></div>
        <div class="flex flex-row gap-2 items-center justify-between">
          <div class="flex flex-row gap-4 flex-wrap">
            <div class="h-8 w-20 bg-gray-300 rounded" v-for="n in 3" :key="n"></div>
          </div>
          <div class="h-8 w-24 bg-gray-300 rounded"></div>
        </div>
      </div>
    </div>
  </div>
</template>

