import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect } from 'vitest';
import MultiSearchableSelect from './MultiSearchableSelect';
import type { SelectOption } from './SearchableSelect';

const options: SelectOption<number>[] = [
  { value: 1, label: 'Alice Smith', sublabel: 'CS' },
  { value: 2, label: 'Bob Jones', sublabel: 'DS' },
  { value: 3, label: 'Carol White', sublabel: 'CS' },
];

function setup(value: number[] = [], onChange = vi.fn()) {
  const user = userEvent.setup();
  const utils = render(
    <MultiSearchableSelect
      options={options}
      value={value}
      onChange={onChange}
      placeholder="Select instructors…"
    />,
  );
  return { user, onChange, ...utils };
}

describe('MultiSearchableSelect', () => {
  it('shows placeholder when nothing is selected', () => {
    setup();
    expect(screen.getByText('Select instructors…')).toBeInTheDocument();
  });

  it('shows chips for each selected value', () => {
    setup([1, 3]);
    expect(screen.getByText('Alice Smith')).toBeInTheDocument();
    expect(screen.getByText('Carol White')).toBeInTheDocument();
    expect(screen.queryByText('Bob Jones')).not.toBeInTheDocument();
  });

  it('opens dropdown on trigger click', async () => {
    const { user } = setup();
    await user.click(screen.getByText('Select instructors…'));
    expect(screen.getByPlaceholderText('Search…')).toBeInTheDocument();
  });

  it('renders all options when dropdown is open', async () => {
    const { user } = setup();
    await user.click(screen.getByText('Select instructors…'));
    expect(screen.getByText('Alice Smith')).toBeInTheDocument();
    expect(screen.getByText('Bob Jones')).toBeInTheDocument();
    expect(screen.getByText('Carol White')).toBeInTheDocument();
  });

  it('shows sublabels in the dropdown', async () => {
    const { user } = setup();
    await user.click(screen.getByText('Select instructors…'));
    expect(screen.getAllByText('CS')).not.toHaveLength(0);
  });

  it('calls onChange with added value when selecting an option', async () => {
    const onChange = vi.fn();
    const { user } = setup([], onChange);
    await user.click(screen.getByText('Select instructors…'));
    await user.click(screen.getByText('Alice Smith'));
    expect(onChange).toHaveBeenCalledWith([1]);
  });

  it('calls onChange with value removed when deselecting an option', async () => {
    const onChange = vi.fn();
    const { user } = setup([1, 2], onChange);
    // Open dropdown — chip area has text "Alice Smith", open via the trigger div
    const trigger = screen.getByText('Alice Smith').closest('div')!;
    await user.click(trigger);
    // Click Alice Smith in the dropdown list (now there are two nodes with that text — chip + list row)
    const buttons = screen.getAllByRole('button');
    const aliceOption = buttons.find(
      (b) => b.textContent?.includes('Alice Smith') && !b.getAttribute('aria-label'),
    );
    expect(aliceOption).toBeDefined();
    await user.click(aliceOption!);
    expect(onChange).toHaveBeenCalledWith([2]);
  });

  it('removes individual chip via × button', async () => {
    const onChange = vi.fn();
    const { user } = setup([1, 2], onChange);
    await user.click(screen.getByRole('button', { name: 'Remove Alice Smith' }));
    expect(onChange).toHaveBeenCalledWith([2]);
  });

  it('filters options by search query', async () => {
    const { user } = setup();
    await user.click(screen.getByText('Select instructors…'));
    await user.type(screen.getByPlaceholderText('Search…'), 'alice');
    expect(screen.getByText('Alice Smith')).toBeInTheDocument();
    expect(screen.queryByText('Bob Jones')).not.toBeInTheDocument();
  });

  it('shows "No results" when search matches nothing', async () => {
    const { user } = setup();
    await user.click(screen.getByText('Select instructors…'));
    await user.type(screen.getByPlaceholderText('Search…'), 'zzz');
    expect(screen.getByText('No results')).toBeInTheDocument();
  });

  it('shows selected count in footer when items are selected', async () => {
    const { user } = setup([1, 2]);
    const trigger = screen.getByText('Alice Smith').closest('div')!;
    await user.click(trigger);
    expect(screen.getByText('2 selected')).toBeInTheDocument();
  });

  it('"Clear all" calls onChange with empty array', async () => {
    const onChange = vi.fn();
    const { user } = setup([1, 2], onChange);
    const trigger = screen.getByText('Alice Smith').closest('div')!;
    await user.click(trigger);
    await user.click(screen.getByText('Clear all'));
    expect(onChange).toHaveBeenCalledWith([]);
  });

  it('does not open when disabled', async () => {
    const user = userEvent.setup();
    render(
      <MultiSearchableSelect options={options} value={[]} onChange={vi.fn()} disabled />,
    );
    await user.click(screen.getByText('Select…'));
    await waitFor(() =>
      expect(screen.queryByPlaceholderText('Search…')).not.toBeInTheDocument(),
    );
  });
});
