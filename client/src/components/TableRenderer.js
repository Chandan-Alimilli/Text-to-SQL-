export default function TableRenderer({ data }) {
  if (!Array.isArray(data) || data.length === 0 || typeof data[0] !== "object")
    return null;

  const headers = [...new Set(data.flatMap((row) => Object.keys(row)))];

  return (
    <div className="mt-6 overflow-x-auto w-full max-w-full">
      <table
        className="w-full table-auto border-collapse bg-white text-black text-sm rounded shadow"
        role="table"
        aria-label="Data table"
      >
        <caption className="text-left text-blue-900 text-3xl font-semibold p-2">
          Data Table
        </caption>
        <thead>
          <tr className="bg-[#1e2237] text-white">
            {headers.map((key, i) => (
              <th key={i} className="p-2 border border-gray-300 text-left">
                {key}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i} className="even:bg-blue-100 odd:bg-blue-200">
              {headers.map((key, j) => (
                <td key={j} className="p-2 border border-gray-500">
                  {typeof row[key] === "object"
                    ? JSON.stringify(row[key])
                    : String(row[key] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
