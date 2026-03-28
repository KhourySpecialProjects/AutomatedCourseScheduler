// import { render, screen } from '@testing-library/react';
// import { MemoryRouter, Route, Routes } from 'react-router-dom';
// import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
// import Schedules from './Schedules';
// import * as useScheduleSectionsModule from '../hooks/useScheduleSections';
// import type { SectionRichResponse } from '../api/generated';

// // Mock child component to isolate the page under test
// vi.mock('../components/ScheduleSectionRowView', () => ({
//   default: ({ sections, scheduleId }: { sections: SectionRichResponse[]; scheduleId: number }) => (
//     <div data-testid="section-row-view" data-schedule-id={scheduleId}>
//       {sections.map((s) => (
//         <div key={s.section_id} data-testid="section-item">
//           {s.course.name}
//         </div>
//       ))}
//     </div>
//   ),
// }));

// const mockSection: SectionRichResponse = {
//   section_id: 1,
//   section_number: 1,
//   capacity: 30,
//   schedule_id: 42,
//   course: { course_id: 10, name: 'Algorithms', description: 'Algo course', credits: 4 },
//   time_block: {
//     time_block_id: 5,
//     days: 'MWR',
//     start_time: '09:00',
//     end_time: '10:30',
//     timezone: 'America/New_York',
//   },
//   instructors: [],
// };

// function renderAtRoute(path: string) {
//   return render(
//     <MemoryRouter initialEntries={[path]}>
//       <Routes>
//         <Route path="/schedules/:scheduleId" element={<Schedules />} />
//         <Route path="/schedules" element={<Schedules />} />
//       </Routes>
//     </MemoryRouter>,
//   );
// }

// describe('Schedules page', () => {
//   let hookSpy: ReturnType<typeof vi.spyOn>;

//   beforeEach(() => {
//     hookSpy = vi.spyOn(useScheduleSectionsModule, 'useScheduleSections');
//   });

//   afterEach(() => {
//     vi.restoreAllMocks();
//   });

//   it('shows spinner while loading', () => {
//     hookSpy.mockReturnValue({ sections: [], loading: true, error: null });
//     renderAtRoute('/schedules/1');
//     expect(screen.getByText('Loading sections…')).toBeInTheDocument();
//     expect(screen.queryByTestId('section-row-view')).not.toBeInTheDocument();
//   });

//   it('shows error message on failure', () => {
//     hookSpy.mockReturnValue({
//       sections: [],
//       loading: false,
//       error: 'Failed to load sections.',
//     });
//     renderAtRoute('/schedules/1');
//     expect(screen.getByText('Failed to load sections.')).toBeInTheDocument();
//     expect(screen.queryByTestId('section-row-view')).not.toBeInTheDocument();
//   });

//   it('renders ScheduleSectionRowView with sections on success', () => {
//     hookSpy.mockReturnValue({ sections: [mockSection], loading: false, error: null });
//     renderAtRoute('/schedules/42');

//     const view = screen.getByTestId('section-row-view');
//     expect(view).toBeInTheDocument();
//     expect(view).toHaveAttribute('data-schedule-id', '42');
//     expect(screen.getByText('Algorithms')).toBeInTheDocument();
//   });

//   it('passes parsed scheduleId from URL to hook', () => {
//     hookSpy.mockReturnValue({ sections: [], loading: false, error: null });
//     renderAtRoute('/schedules/7');
//     expect(hookSpy).toHaveBeenCalledWith(7);
//   });

//   it('falls back to scheduleId=1 when param is absent', () => {
//     hookSpy.mockReturnValue({ sections: [], loading: false, error: null });
//     renderAtRoute('/schedules');
//     expect(hookSpy).toHaveBeenCalledWith(1);
//   });

//   it('renders page heading', () => {
//     hookSpy.mockReturnValue({ sections: [], loading: false, error: null });
//     renderAtRoute('/schedules/1');
//     expect(screen.getByRole('heading', { name: 'Schedule' })).toBeInTheDocument();
//   });

//   it('does not render both spinner and table simultaneously', () => {
//     hookSpy.mockReturnValue({ sections: [mockSection], loading: true, error: null });
//     renderAtRoute('/schedules/1');
//     // loading=true: spinner shown, table hidden
//     expect(screen.getByText('Loading sections…')).toBeInTheDocument();
//     expect(screen.queryByTestId('section-row-view')).not.toBeInTheDocument();
//   });
// });
