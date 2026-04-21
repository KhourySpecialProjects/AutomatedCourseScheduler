import { instance } from '../api/axiosInstance';

export async function downloadScheduleCsv(scheduleId: number): Promise<void> {
  const response = await instance.get(`/schedules/${scheduleId}/export/csv`, {
    responseType: 'blob',
  });
  const url = URL.createObjectURL(new Blob([response.data as BlobPart]));
  const a = document.createElement('a');
  a.href = url;
  a.download = `schedule_${scheduleId}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
