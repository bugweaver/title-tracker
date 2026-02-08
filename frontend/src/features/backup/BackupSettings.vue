<script setup lang="ts">
import { ref } from 'vue';
import { apiClient } from '@/shared/api';

const isExporting = ref(false);
const isImporting = ref(false);
const importError = ref<string | null>(null);
const importSuccess = ref<string | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);

const handleExport = async () => {
    isExporting.value = true;
    try {
        const blob = await apiClient.getBlob('/backup/export');
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        
        // Use default filename as we can't easily get headers from getBlob currently 
        // without changing the signature. 
        // Or we can just generate it client side which is fine.
        let filename = `backup_${new Date().toISOString().split('T')[0]}.txt`;
        
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Export failed:', error);
        alert('Не удалось скачать резервную копию');
    } finally {
        isExporting.value = false;
    }
};

const triggerImport = () => {
    fileInput.value?.click();
};

const handleFileChange = async (event: Event) => {
    const target = event.target as HTMLInputElement;
    if (!target.files || target.files.length === 0) return;
    
    const file = target.files[0];
    if (!file) return;
    await handleImport(file);
    
    // Reset input
    target.value = '';
};

const handleImport = async (file: File) => {
    isImporting.value = true;
    importError.value = null;
    importSuccess.value = null;
    
    const formData = new FormData();
    formData.append('data', file);
    
    try {
        const response = await apiClient.postFormData<{ processed_count: number }>('/backup/import', formData);
        
        const count = response.processed_count;
        importSuccess.value = `Успешно импортировано ${count} тайтлов`;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (error: any) {
        console.error('Import failed:', error);
        importError.value = error.response?.data?.message || 'Ошибка при импорте';
    } finally {
        isImporting.value = false;
    }
};
</script>

<template>
    <div class="bg-background-soft rounded-xl border border-border p-6">
        <h2 class="text-xl font-bold mb-4 text-text">Резервное копирование</h2>
        <p class="text-text-muted p-2">
            Вы можете выгрузить всю вашу библиотеку в файл для хранения, 
            или загрузить её обратно. При импорте существующие записи будут обновлены.
        </p>
        
        <div class="flex flex-col sm:flex-row gap-4">
            <button 
                @click="handleExport" 
                :disabled="isExporting"
                class="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
            >
                <span v-if="isExporting" class="animate-spin">⏳</span>
                <span>{{ isExporting ? 'Экспорт...' : 'Скачать резервную копию' }}</span>
            </button>
            
            <div class="relative">
                <input 
                    type="file" 
                    ref="fileInput" 
                    accept=".txt,.json" 
                    class="hidden" 
                    @change="handleFileChange"
                />
                <button 
                    @click="triggerImport" 
                    :disabled="isImporting"
                    class="px-4 py-2 border border-border text-text rounded-lg hover:bg-surface-hover disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
                >
                    <span v-if="isImporting" class="animate-spin">⏳</span>
                    <span>{{ isImporting ? 'Импорт...' : 'Загрузить из файла' }}</span>
                </button>
            </div>
        </div>
        
        <div v-if="importSuccess" class="mt-4 p-3 bg-green-500/10 text-green-500 rounded-lg border border-green-500/20">
            {{ importSuccess }}
        </div>
        
        <div v-if="importError" class="mt-4 p-3 bg-red-500/10 text-red-500 rounded-lg border border-red-500/20">
            {{ importError }}
        </div>
    </div>
</template>
