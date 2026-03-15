import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import SectionsTable from './SectionsTable';
import type { SectionResponse } from '../api/generated';

const mockSections: SectionResponse[] = [
  {
    SectionID: 1,
    Schedule: 10,
    TimeBlock: 2,
    Course: 101,
    Capacity: 30,
    Instructor: 5,
  },
  {
    SectionID: 2,
    Schedule: null,
    TimeBlock: null,
    Course: null,
    Capacity: null,
    Instructor: null,
  },
];

describe('SectionsTable', () => {
  it('renders a row for each section', () => {
    render(<SectionsTable sections={mockSections} />);
    expect(screen.getAllByRole('row')).toHaveLength(mockSections.length + 1); // +1 for header
  });

  it('displays section data in cells', () => {
    render(<SectionsTable sections={mockSections} />);
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('30')).toBeInTheDocument();
  });

  it('renders em dash for null fields', () => {
    render(<SectionsTable sections={mockSections} />);
    const dashes = screen.getAllByText('—');
    expect(dashes.length).toBe(5); // section 2 has 5 null fields
  });

  it('shows empty state when no sections', () => {
    render(<SectionsTable sections={[]} />);
    expect(screen.getByText('No sections found.')).toBeInTheDocument();
  });
});
