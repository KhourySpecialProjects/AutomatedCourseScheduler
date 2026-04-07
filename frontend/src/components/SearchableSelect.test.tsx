import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect } from 'vitest';
import SearchableSelect, { type SelectOption } from './SearchableSelect';

const options: SelectOption<number>[] = [
  { value: 1, label: 'Algorithms', sublabel: 'CS 3000' },
  { value: 2, label: 'Data Structures', sublabel: 'CS 2000' },
  { value: 3, label: 'Operating Systems', sublabel: 'CS 3650' },
];

function setup(value: number | null = null, onChange = vi.fn()) {
  const user = userEvent.setup();
  const utils = render(
    <SearchableSelect
      options={options}
      value={value}
      onChange={onChange}
      placeholder="Pick a course…"
    />,
  );
  return { user, onChange, ...utils };
}

describe('SearchableSelect', () => {
  it('shows placeholder when no value is selected', () => {
    setup();
    expect(screen.getByText('Pick a course…')).toBeInTheDocument();
  });

  it('shows the selected option label', () => {
    setup(2);
    expect(screen.getByText('Data Structures')).toBeInTheDocument();
  });

  it('opens dropdown on trigger click', async () => {
    const { user } = setup();
    await user.click(screen.getByRole('button'));
    expect(screen.getByPlaceholderText('Search…')).toBeInTheDocument();
  });

  it('renders all options when dropdown is open', async () => {
    const { user } = setup();
    await user.click(screen.getByRole('button'));
    expect(screen.getByText('Algorithms')).toBeInTheDocument();
    expect(screen.getByText('Data Structures')).toBeInTheDocument();
    expect(screen.getByText('Operating Systems')).toBeInTheDocument();
  });

  it('shows sublabels in the dropdown', async () => {
    const { user } = setup();
    await user.click(screen.getByRole('button'));
    expect(screen.getByText('CS 3000')).toBeInTheDocument();
  });

  it('filters options based on search query', async () => {
    const { user } = setup();
    await user.click(screen.getByRole('button'));
    await user.type(screen.getByPlaceholderText('Search…'), 'data');

    expect(screen.getByText('Data Structures')).toBeInTheDocument();
    expect(screen.queryByText('Algorithms')).not.toBeInTheDocument();
    expect(screen.queryByText('Operating Systems')).not.toBeInTheDocument();
  });

  it('shows "No results" when search matches nothing', async () => {
    const { user } = setup();
    await user.click(screen.getByRole('button'));
    await user.type(screen.getByPlaceholderText('Search…'), 'zzz');
    expect(screen.getByText('No results')).toBeInTheDocument();
  });

  it('calls onChange with the option value on selection', async () => {
    const onChange = vi.fn();
    const { user } = setup(null, onChange);
    await user.click(screen.getByRole('button'));
    await user.click(screen.getByText('Algorithms'));
    expect(onChange).toHaveBeenCalledWith(1);
  });

  it('closes the dropdown after selecting an option', async () => {
    const { user } = setup();
    await user.click(screen.getByRole('button'));
    await user.click(screen.getByText('Algorithms'));
    await waitFor(() =>
      expect(screen.queryByPlaceholderText('Search…')).not.toBeInTheDocument(),
    );
  });

  it('shows a checkmark next to the currently selected option', async () => {
    const { user } = setup(2);
    await user.click(screen.getByRole('button'));
    // The selected "Data Structures" option should have a checkmark svg
    const optionButtons = screen.getAllByRole('button');
    // Find the Data Structures option button (not the trigger)
    const dsButton = optionButtons.find((b) => b.textContent?.includes('Data Structures'));
    expect(dsButton).toBeDefined();
    // Has a check svg (aria or visual) — check that the button has the selected styling
    expect(dsButton?.querySelector('svg')).toBeInTheDocument();
  });

  it('is disabled when the disabled prop is set', async () => {
    render(
      <SearchableSelect options={options} value={null} onChange={vi.fn()} disabled />,
    );
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
