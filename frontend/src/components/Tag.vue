<template>
  <span class="tag" :class="`tag-${type}`"><slot /></span>
</template>

<script setup>
// type: blue | green | orange | red | purple | teal | gray
defineProps({
  type: { type: String, default: 'gray' },
})
</script>

<style scoped>
.tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--r-full);
  font-size: var(--fs-xs);
  line-height: 1.6;
  white-space: nowrap;
}

.tag-blue { background: var(--c-primary-weak); color: var(--c-primary); }
.tag-green { background: var(--c-success-weak); color: var(--c-success); }
.tag-orange { background: var(--c-warning-weak); color: var(--c-warning); }
.tag-red { background: var(--c-danger-weak); color: var(--c-danger); }
.tag-purple { background: var(--c-purple-weak); color: var(--c-purple); }
.tag-teal { background: var(--c-teal-weak); color: var(--c-teal); }
.tag-gray { background: var(--c-bg); color: var(--c-text-3); }
</style>
